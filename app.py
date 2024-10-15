import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
from werkzeug.utils import secure_filename
from s3_utils import download_file_from_s3, upload_blank_file_to_s3
from utils import allowed_file
import logging
from logging.handlers import RotatingFileHandler
from celery_config import make_celery
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError
from config import Config
from celery import shared_task

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure the app with settings from Config
app.config.from_object(Config)

# Add Celery configuration
app.config.update(
    CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379'),
    CELERY_RESULT_BACKEND=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379')
)

# Ensure AWS configuration is loaded
app.config['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
app.config['AWS_DEFAULT_REGION'] = os.getenv('AWS_DEFAULT_REGION')
app.config['S3_BUCKET'] = os.getenv('S3_BUCKET')

# Initialize Celery with the Flask app
celery = make_celery(app)

# Import the task after initializing Celery
from adult_report_generator import generate_full_report

# Set up logging
log_folder = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(log_folder, 'app.log')
file_handler = RotatingFileHandler(log_file_path, maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('PAR application startup')

# Initialize S3 client with AWS credentials from environment variables
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

# Ensure the upload and output folders exist
upload_folder = os.getenv('UPLOAD_FOLDER', './uploads')
output_folder = os.getenv('OUTPUT_FOLDER', './outputs')
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)


# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.info("Index route accessed")
    if request.method == 'POST':
        app.logger.info("POST request received")
        session_id = str(uuid.uuid4())
        app.logger.info(f"Generated session ID: {session_id}")
        session['id'] = session_id

        s3_folder = f"uploads/{session_id}/"
        user_output_folder = os.path.join(output_folder, session_id)
        app.logger.info(f"Created S3 folder: {s3_folder}, output folder: {user_output_folder}")

        os.makedirs(user_output_folder, exist_ok=True)

        required_files = {
            'Transcript.pdf', 'IntakeForm_Results.pdf', 'CATQ_Results.pdf',
            'GAD_Results.pdf', 'GARS_Results.pdf', 'KBIT_Results.pdf',
            'RAADSR_Results.pdf', 'SRS2_Results.pdf', 'Vineland_Results.pdf'
        }

        uploaded_files = request.files.getlist('assessment_files')
        uploaded_filenames = set()
        s3_paths = {}

        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                s3_key = s3_folder + filename
                try:
                    s3.upload_fileobj(file, os.getenv('S3_BUCKET'), s3_key)
                    uploaded_filenames.add(filename)
                    s3_paths[filename] = s3_key
                    app.logger.info(f"Uploaded file to S3: {s3_key}")
                    
                    # Verify the upload
                    s3.head_object(Bucket=os.getenv('S3_BUCKET'), Key=s3_key)
                    app.logger.info(f"Verified file exists in S3: {s3_key}")
                except NoCredentialsError:
                    app.logger.error("S3 credentials not available")
                    return "S3 credentials not available", 500
                except Exception as e:
                    app.logger.error(f"Error uploading file to S3: {str(e)}")
                    app.logger.error(f"Bucket: {os.getenv('S3_BUCKET')}")
                    app.logger.error(f"Key: {s3_key}")
                    app.logger.error(f"File object type: {type(file)}")
                    return f"Error uploading file to S3: {str(e)}", 500
            else:
                app.logger.error(f"Invalid file: {file.filename}")
                return f"Invalid file: {file.filename}", 400

        # Handle missing files
        missing_files = required_files - uploaded_filenames
        for missing_file in missing_files:
            s3_path = upload_blank_file_to_s3(
                missing_file, 
                session_id, 
                app.config['AWS_ACCESS_KEY_ID'],
                app.config['AWS_SECRET_ACCESS_KEY'],
                app.config['AWS_DEFAULT_REGION'],
                app.config['S3_BUCKET']
            )
            if s3_path:
                s3_paths[missing_file] = s3_path
            else:
                app.logger.error(f"Failed to create blank file for: {missing_file}")
                return f"Failed to create blank file for: {missing_file}", 500

        app.logger.info("Enqueuing background task")
        try:
            task = generate_full_report.delay(
                session_id, 
                s3_paths, 
                user_output_folder,
                app.config['AWS_ACCESS_KEY_ID'],
                app.config['AWS_SECRET_ACCESS_KEY'],
                app.config['AWS_DEFAULT_REGION'],
                app.config['S3_BUCKET']
            )
            session['task_id'] = task.id
            app.logger.info(f"Background task enqueued with ID: {task.id}")
            return redirect(url_for('processing'))
        except Exception as e:
            app.logger.error(f"Error enqueuing background task: {str(e)}")
            return render_template('error.html', error_message="An error occurred while processing your request. Please try again later."), 500

    else:
        app.logger.info("Rendering index page")
        return render_template('index.html', current_year=datetime.now().year)

@app.route('/processing')
def processing():
    app.logger.info("Processing route accessed")
    task_id = session.get('task_id')
    if not task_id:
        app.logger.warning("No task ID found in session, redirecting to index")
        return redirect(url_for('index'))

    task = generate_full_report.AsyncResult(task_id)
    app.logger.info(f"Task state: {task.state}")
    if task.state == 'PENDING':
        app.logger.info(f"Task {task_id} is still pending")
        return render_template('processing.html')
    elif task.state in ['FAILURE', 'REVOKED']:
        app.logger.error(f"Task {task_id} failed: {str(task.result)}")
        return "Task failed", 500
    elif task.state == 'SUCCESS':
        app.logger.info(f"Task {task_id} completed successfully")
        result = task.result
        if isinstance(result, dict) and 'status' in result:
            if result['status'] == 'success':
                app.logger.info("Redirecting to results")
                session['s3_report_path'] = result['s3_path']
                return redirect(url_for('results'))
            else:
                app.logger.error(f"Task completed with error: {result.get('message', 'Unknown error')}")
                return "Task failed", 500
        else:
            app.logger.error(f"Unexpected task result: {result}")
            return "Unexpected task result", 500
    else:
        app.logger.info(f"Task {task_id} in unknown state: {task.state}")
        return "Task status unknown", 500
    
@app.route('/results')
def results():
    app.logger.info("Results route accessed")
    s3_report_path = session.get('s3_report_path')
    if not s3_report_path:
        app.logger.warning("No S3 report path found in session, redirecting to processing")
        return redirect(url_for('processing'))

    try:
        s3.head_object(Bucket=os.getenv('S3_BUCKET'), Key=s3_report_path)
        app.logger.info("Report found in S3, rendering results page")
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': os.getenv('S3_BUCKET'), 'Key': s3_report_path},
            ExpiresIn=3600  # URL valid for 1 hour
        )
        return render_template('results.html', download_url=presigned_url, current_year=datetime.now().year)
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            app.logger.warning("Report not found in S3, redirecting to processing")
            return redirect(url_for('processing'))
        else:
            app.logger.error(f"Error checking S3 for report: {e}")
            return "An error occurred", 500

@app.route('/download_file')
def download_file():
    session_id = session.get('id')
    file_path = f"{session_id}/generated_par.pdf"

    try:
        local_path = '/tmp/generated_par.pdf'
        download_file_from_s3(
            file_path, 
            local_path,
            app.config['AWS_ACCESS_KEY_ID'],
            app.config['AWS_SECRET_ACCESS_KEY'],
            app.config['AWS_DEFAULT_REGION'],
            app.config['S3_BUCKET']
        )
        
        with open(local_path, 'rb') as f:
            response = make_response(f.read())
        
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=generated_par.pdf'
        
        return response
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        return "Error downloading file", 500

@app.route('/test_s3')
def test_s3():
    try:
        s3.list_buckets()
        return "Successfully connected to S3 and listed buckets", 200
    except Exception as e:
        app.logger.error(f"Error connecting to S3: {str(e)}")
        return f"Error connecting to S3: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=app.config['DEBUG'], port=5000)
