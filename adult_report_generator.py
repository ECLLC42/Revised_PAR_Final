import os
import logging
from io import BytesIO
from celery import shared_task
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import markdown2
from logging.handlers import RotatingFileHandler
from s3_utils import get_s3_client, download_file_from_s3_to_memory, upload_bytes_to_s3
from utils import extract_text_from_pdf_bytes
from config import config
from utils import simple_markdown_to_pdf
print(f"simple_markdown_to_pdf function: {simple_markdown_to_pdf}")

# Set up logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
log_file = 'report_generator.log'
log_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 100, backupCount=20)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.DEBUG)

logger = logging.getLogger('report_generator')
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

# Initialize API client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_cover_page():
    return """
CONFIDENTIAL Psychological Assessment Report

Patient's Name: 
Date of Report:
Examiner: Joshua M. Henderson, PhD

CONFIDENTIAL DOCUMENT

This document contains confidential and privileged information intended only for the individual named above. If you are not the intended recipient, please notify the sender immediately and delete this document. Any unauthorized review, use, disclosure, or distribution is prohibited.
"""

def generate_table_of_contents():
    return """
Table of Contents

1. Patient Identification and Referral Information
2. Informed Consent
3. Collaterals Involved
4. Background Information
   a. Family History and Composition
   b. Developmental History
   c. Educational History
   d. Medical and Psychiatric History
5. Assessment Procedures and Results
6. Behavioral Observations
7. Documentation of Validity Challenges
8. Mental Status Examination (MSE)
9. DSM-5 Diagnostic Criteria for Autism Spectrum Disorder
10. Strengths and Challenges
11. Risk and Protective Factors
12. Recommendations
13. Prognosis
14. Follow-Up Plan
15. Interpretive Summary
16. Conclusion
17. Resources
18. References
19. DSM-5 Diagnostic Criteria Table
"""

def generate_cover_and_toc():
    cover_page = generate_cover_page()
    table_of_contents = generate_table_of_contents()
    return cover_page + "\n\n" + table_of_contents
# The rest of your code (generate_sections_1_3, generate_section_4, etc.) follows...

def generate_sections_1_3(intakeform_text, transcript_text):
    prompt = f"""
Based on the following intake form and transcript, generate Sections I, II, and III of the Psychological Assessment Report (PAR). Use markdown formatting for headers and bullet points.

## I. Patient Identification and Reason for Referral
- Include patient's name, date of birth, home address, and physical location during remote assessment.
- State the reason for referral, including age, presenting concerns, and who conducted the evaluation.

## II. Informed Consent and Assessment Scope
- Summarize the informed consent process, including details provided and agreed upon.
- Outline the assessment scope, including domains covered and reasons for selecting specific assessments.

## III. Collateral Information
- List individuals providing information and assessments used.

Use professional language appropriate for a psychological assessment report.

Intake Form:
{intakeform_text}

Transcript:
{transcript_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating Sections I, II, and III of a Psychological Assessment Report based on provided information. Use markdown formatting for headers and bullet points."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def generate_section_4(intakeform_text, transcript_text):
    prompt = f"""
Using the following intake form and transcript, generate Section IV (Background Information) of the Psychological Assessment Report. Include detailed information in the following subsections:

IV. Background Information

Family History and Composition:
- Provide detailed information about the patient's family, including parental background, family medical and psychiatric history, and current household composition.

Developmental History:
- Outline developmental milestones, any delays, and early signs of atypical neurodevelopment.

Educational/Occupational History:
- Describe the patient's educational journey, academic achievements, and occupational history, including any challenges faced.

Medical and Psychiatric History:
- Detail medical conditions, psychiatric diagnoses, treatments received, medications, and sensory sensitivities.

Use professional language and ensure the content aligns with the structure provided.

An example of a simulated perfect response for this section is: 
IV. Background Information

Family History and Composition:

Sophie has a profound and complicated familial history, relevant both to neurodevelopmental and psychiatric conditions. Sophies biological mother, Mary, currently 57 years old, works as a Sales Specialist and possesses a high school education. Her life has been shadowed by a spectrum of psychological issues, including emotional disturbance and chronic anxiety, which were prevalent during her pregnancy with Sophie. The biological father, Robert, aged 56, is on disability and his educational attainment did not exceed the 11th grade. The father's side of the family is notable for an extensive history of severe psychiatric disorders and chronic medical conditions. These conditions include, but are not limited to: schizophrenia, emotional disturbances, severe head injuries, migraine headaches, Alzheimers disease, depression, reading problems, high blood pressure, stroke, abuse, speech/language delay, and a range of behavioral disorders including aggressive/defiant behaviors and antisocial behavior.

Sophies immediate family also includes a younger sister diagnosed with attention deficit disorder (ADD), intensifying the neuropsychological predispositions within the family unit. The parents' draconian disciplinary techniques, including frequent grounding and corporal punishment, likely amplified an environment of continual psychological distress and fear for Sophie, reinforcing an embedded fear of failure and social acceptance.

Her current household includes her husband, aged 43, who serves as her primary caretaker due to her severe Crohns Disease. It's pertinent that the couple previously housed an abusive stepdaughter, whose presence created considerable stress and exacerbated familial discord.

Developmental History:

Sophie showed a developmental trajectory with notable delays and early signs of atypical neurodevelopment. She achieved sitting unaided at five months, crawling at seven months, and walking unaided at twelve months. These milestones indicate a relatively standard course of gross motor development, yet her progression in social communication raised early concerns. Sophie began babbling at two months, progressed to single words by nine months, and advanced to short phrases by eighteen months. These linguistic milestones were within the normative range but require contextual interpretation given the subsequent emergence of social and communicative anomalies. 
As early as age five, Sophie displayed indications of profound social isolation and hyper fixation on single pursuits, notably singing, which could suggest early signs of ASD. Her interest in singing became singularly intense, evolving into a potential diagnostic marker for obsessive tendencies inherent in ASD.
By nine years old, Sophie's interactions with peers significantly dwindled, favoring solitude and independent activities. This social withdrawal became more evident and persistent, culminating in a landscape of social dysfunction that has substantially worsened in the past decade.

Educational/Occupational History:

Sophie's educational trajectory was punctuated by significant academic achievements despite innumerable personal and psychological challenges. She attended multiple schools but has profound memory issues impeding specific recollections of early education. Despite this, she achieved a GPA of 3.66 upon high school graduation, engaging in Advanced Placement (AP) coursework. These were accomplished concomitantly with unconventional academic strategies such as cheating, highlighting a need for adaptive mechanisms to mitigate her cognitive and environmental challenges.

Sophie's passion for singing began at a notably young age, with professional aspirations towards opera. Despite her evident talent, financial and logistic disruptions, including an incomplete FAFSA loan causing the non-release of her transcripts, dismantled her college pursuits. Consequently, Sophie transitioned into the workforce, gravitating towards administrative roles post her college withdrawal.

Her professional life encompasses various administrative positions, evolving significantly since her initial customer service roles in companies such as Expedia. Each role has demanded exhaustive cognitive and emotional resources, undermining Sophie's mental health reflected in frequent professional-induced meltdowns. Currently employed as an Executive Assistant (EA), Sophie supports high-level executives by performing intricate administrative tasks. Despite the apparent manageability of her responsibilities, the pervasive office politics, hierarchical ego battles, and necessity to engage in small talk exacerbate her ASD-related social anxiety and sensory overload.

Medical and Psychiatric History:

Sophie's extensive medical history aligns with her deeply rooted psychiatric and developmental challenges. She has been diagnosed with Crohns Disease, Proctitis, Diverticulosis, Polyps, Gastritis, and an Esophageal Structure, necessitating numerous colonoscopies and endoscopies. To mitigate the severity of these conditions, Sophie adheres to a strict Specific Carbohydrate Diet. Her reproductive history includes Polycystic Ovary Syndrome (PCOS), hypothyroidism, and endometriosis, further complicating her physical health profile.

Psychiatrically, Sophie has been diagnosed with depression, anxiety, Posttraumatic Stress Disorder (PTSD), Premenstrual Dysphoric Disorder (PMDD), and ADHD Combined Type. Despite diverse therapeutic interventions ranging from psychiatric counseling to pharmacological treatment, Sophie faces considerable hurdles in managing her symptoms, demonstrated by her prevalent sensory sensitivities and frequent psychomotor agitation.

Sophie has been on various medications such as Avsola biologic infusions, Flexiril, and Dilaudid. The presence of a supportive and responsive husband significantly improves adherence to these treatment regimens.

Her sensory sensitivities include severe intolerance to specific auditory and visual stimuli—an overstimulation consequence often requiring environmental adjustments like earplugs and avoiding fluorescent lights. Sophie's psychiatric conditions, chronic physical health issues, and complex sensory sensitivities create an intertwined feedback loop aggravating her mental health.

The profound stress causes frequent meltdowns and psychosocial impairments, prompting Sophie to seek evaluations for Autism Spectrum Disorder (ASD) to understand and manage lifelong challenges effectively. Her struggle to balance household responsibilities, amplified by her husband's ADHD and the need for intricate daily routines, underscores the necessity for structured support and a comprehensive management plan.

Sophie presents a multifaceted profile indicative of significant developmental, familial, medical, and psychiatric complexities. The intersectionality of her longitudinal struggles underscores the need for rigorous, multi-disciplinary, and holistic diagnostic evaluations and interventional strategies. Accentuating this, the possibility of ASD profoundly permeates her actions, interactions, and perceptions, warranting expansive diagnostic scrutiny and tailored therapeutic approaches. This nuanced understanding will be pivotal in optimizing Sophie's functionality, elevating her quality of life, and mitigating the risks emanating from her diverse healthcare needs.


Intake Form:
{intakeform_text}

Transcript:
{transcript_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating the Background Information section of a Psychological Assessment Report based on provided information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content

def generate_section_5(test_results_texts):
    test_results_combined = '\n\n'.join([f"{test_name} Results:\n{text}" for test_name, text in test_results_texts.items()])
    prompt = f"""
Based on the following test results, generate Section V (Assessment Measures) of the Psychological Assessment Report. Use markdown formatting for headers and bullet points. For each assessment, include:

- A brief description of the assessment's purpose.
- The patient's scores and percentiles.
- An interpretation of the results.

Ensure to cover the following assessments:

- Vineland Adaptive Behavior Scales, Third Edition (Vineland-3)
- Social Responsiveness Scale, Second Edition (SRS-2)
- Gilliam Autism Rating Scale, Third Edition (GARS-3)
- Brief Observation of Symptoms of Autism (BOSA-F2)
- Generalized Anxiety Disorder 7-item (GAD-7) Scale
- Ritvo Autism Asperger Diagnostic Scale-Revised (RAADS-R)
- Kaufman Brief Intelligence Test, Second Edition (KBIT-2)
- Camouflaging Autistic Traits Questionnaire (CAT-Q)

Use professional language and align with the structure provided.

{test_results_combined}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating the Assessment Measures section of a Psychological Assessment Report based on provided test results. Use markdown formatting for headers and bullet points."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_sections_6_7(intakeform_text, transcript_text):
    prompt = f"""
Using the following intake form and transcript, generate Sections VI and VII of the Psychological Assessment Report.

VI. Behavioral Observations
- Describe observed behaviors consistent with assessment data.
- Provide specific examples illustrating social avoidance, adaptive strategies, and any notable behaviors.

VII. Mental Status Examination
- General Appearance
- Behavior
- Speech
- Mood and Affect
- Cognition
- Sensory Processing

Use professional language and ensure the content aligns with the structure provided.

An example of a simulated perfect response for this section is: 

VI. Behavioral Observations

Sophie exhibited behaviors consistent with this reports assessment data indicating significant social avoidance and difficulty forming peer connections. For example, her interactions were marked by masking and mirroring, indicating adaptive strategies to manage social challenges. She showed a strong preference for solitude and hypersensitivity to sensory stimuli, such as noise and crowds, often leading to withdrawal. Sophie's reliance on a few deep connections rather than a broad social network highlights her selective social engagement. These behaviors, coupled with her reflections on past trauma and familial dynamics, provide a nuanced understanding of her adaptive mechanisms and emotional struggles.

VII. Mental Status Examination

- General Appearance: Sophie appeared well-groomed, though her speech occasionally revealed emotional distress and anxiety, particularly in response to sensory stimuli.

- Behavior: Repetitive behaviors, such as skin biting and rocking, were observed as self-soothing mechanisms in response to overstimulation or social anxiety. Her mirroring of conversational patterns suggested a conscious effort to connect more openly.

- Speech: Sophie communicated verbally with a rich vocabulary, though her speech often became tangential and deeply expressive, especially on topics of personal interest, which could be challenging to follow.

- Mood and Affect: Her mood fluctuated between anxiety and reflection, with feelings of anger and helplessness emerging during discussions of unexpected social situations. Her affect was congruent with her reported emotions, indicating authenticity in her emotional expression.

- Cognition: Sophie demonstrated cognitive engagement by following directions effectively, though she reported difficulties with attention unless focused on special interests, consistent with her ADHD diagnosis.

- Sensory Processing: She exhibited pronounced reactions to sensory overload, such as bright lights and loud noises, causing significant discomfort and often impeding her ability to engage or respond typically in social environments.

Intake Form:
{intakeform_text}

Transcript:
{transcript_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating the Behavioral Observations and Mental Status Examination sections of a Psychological Assessment Report based on provided information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content

def generate_section_8(test_results_texts):
    test_results_combined = '\n\n'.join([f"{test_name} Results:\n{text}" for test_name, text in test_results_texts.items()])
    prompt = f"""
Based on the following test results, generate Section VIII (Interpretation) of the Psychological Assessment Report. Provide:

- An interpretation of each assessment result.
- A synthesis that integrates findings across assessments.
- Discuss how the results relate to the patient's functioning.

Use professional language and ensure the content aligns with the structure provided.

An example of a simulated perfect response for this section is: 

VIII. Interpretation

Vineland Adaptive Behavior Scales, Third Edition (Vineland-3)
Sophies Vineland-3 results reveal significant challenges in adaptive functioning, particularly in communication and socialization. Her Adaptive Behavior Composite score of 78, along with subscale scores of 73 in Communication (4th percentile) and 69 in Socialization (2nd percentile), indicate notable difficulties in these areas. Specifically, Sophie struggles with understanding and processing verbal communication, conveying thoughts and emotions, and engaging in social interactions. These challenges may contribute to feelings of isolation and frustration.
Conversely, Sophie's Daily Living Skills score of 101 (53rd percentile) suggests she can manage everyday tasks effectively. This relative strength provides a foundation for further development of adaptive behaviors, showcasing that with targeted interventions, there are opportunities for improved functioning in more challenging areas such as communication and socialization.

Social Responsiveness Scale, Second Edition (SRS-2)
The SRS-2 results suggest generally normal social functioning for Sophie, with a Total T-score of 53. However, mild difficulties are noted in social communication (T-score: 54) and social motivation (T-score: 57). No clinically concerning repetitive behaviors were observed (T-score: 50). These findings indicate that while Sophie functions well socially overall, she may benefit from strategies to enhance her social communication and motivation.

Gilliam Autism Rating Scale, Third Edition (GARS-3)
Sophie's Autism Index score of 84 on the GARS-3 suggests a "very likely" presence of Autism Spectrum Disorder (ASD). She faces significant challenges in social interaction (SI: 7, 16th percentile) and social communication (SC: 6, 9th percentile), but demonstrates strong cognitive skills (CS: 13, 84th percentile). These results underscore the need for comprehensive interventions to address her social and communication challenges while leveraging her cognitive strengths.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with interpreting assessment results for a Psychological Assessment Report."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_sections_9_11(all_texts):
    all_text_combined = '\n\n'.join([f"{key}:\n{value}" for key, value in all_texts.items()])
    prompt = f"""
Based on all the provided information, generate Sections IX, X, and XI of the Psychological Assessment Report.

IX. DSM-5 Criteria for Autism Spectrum Disorder
- Match the patient's symptoms to DSM-5 criteria for ASD.
- Provide specific examples and assessment data supporting each criterion.

X. Strengths and Challenges
- List the patient's strengths, leveraging assessment data.
- Outline challenges, including social communication and emotional regulation.

XI. Risk and Protective Factors
- Identify risk factors impacting prognosis.
- Highlight protective factors that can aid in intervention.

Use professional language and ensure the content aligns with the structure provided.

A simulated perfect response for this section is: 

IX. DSM-5 Criteria for Autism Spectrum Disorder
A1. Persistent Deficits in Social Communication and Social Interaction:

- Social Communication: Sophie's GARS-3 score of 6 in Social Communication and SRS-2 T-score of 54 are indicative of significant challenges in reciprocal conversation and understanding social nuances. Behavioral observations in therapy sessions reveal a marked tendency to use tangential speech and difficulty in interpreting social cues. For example, Sophie often misinterprets figurative language and struggles to maintain the flow of conversation, frequently veering off-topic. This aligns with the DSM-5 criteria for deficits in social-emotional reciprocity, where impaired back-and-forth conversation and reduced sharing of interests, emotions, or affect are evident.
- Social Interaction: The RAADS-R score of 50 in Social Relatedness and Vineland-3 Socialization score of 69 highlight notable difficulties in forming and maintaining social relationships. In clinical observations, Sophie prefers solitary activities and shows discomfort in group settings. She maintains few close relationships, primarily with family members and her husband, reflecting significant challenges in developing and maintaining broader social networks. This behavior is consistent with the DSM-5 criterion for deficits in developing, maintaining, and understanding relationships, where there is an evident lack of interest in peers and difficulty adjusting behavior to suit various social contexts.

A2. Restricted, Repetitive Patterns of Behavior, Interests, or Activities:

- Repetitive Behaviors: The GARS-3 score of 8 in Restricted/Repetitive Behaviors and SRS-2 T-score of 50 in Restricted Interests and Repetitive Behavior underscore the presence of stereotyped actions and restricted interests. Behavioral examples include Sophie's hyperfixation on singing and spiritual topics, where she can engage in these activities for prolonged periods without losing interest. Additionally, her stimming behaviors, such as biting the skin off her fingertips and leg bouncing (previously), are observed in therapy sessions and daily self-reports. These behaviors meet the DSM-5 criterion for the presence of stereotyped or repetitive motor movements, use of objects, or speech, and insistence on sameness with inflexible adherence to routines.

A3. Symptoms Present in Early Developmental Period:

- Sophie's developmental history indicates early signs consistent with ASD. Early childhood records and parental reports highlight delayed milestones in social engagement and a marked preference for solitary play. For example, as a child, she would often engage in repetitive singing for hours and showed little interest in interactive play with peers. These traits were evident from a young age and align with the DSM-5 criterion that specifies the presence of symptoms in the early developmental period.

A4. Symptoms Cause Clinically Significant Impairment:

- The impact of these symptoms on Sophie's daily functioning is profound, as evidenced by her difficulty with social integration, communication, and emotional regulation across various assessments. For instance, she reports frequent challenges in maintaining employment due to miscommunications with colleagues and overwhelming stress in social work environments. Furthermore, Sophie's inability to engage in social activities without considerable anxiety has led to an isolated lifestyle, exacerbating her mental health issues. These behaviors fulfill the DSM-5 criterion for clinically significant impairment in social, occupational, or other important areas of current functioning.

X. Strengths and Challenges
Strengths:

- Cognitive Abilities: Sophie's nonverbal IQ score of 106 on the KBIT-2 suggests strengths in visual-spatial reasoning and pattern recognition. These abilities can be leveraged in structured learning environments and tasks that require problem-solving and logical reasoning.
- Intense Interests: Her strong cognitive style and intense interests, as indicated by the GARS-3 Cognitive Style score of 13, can be harnessed to engage her in meaningful activities and learning opportunities. These interests can serve as a motivational tool in educational and therapeutic settings.

Challenges:

- Social Communication: Significant difficulties in social communication and interaction, as highlighted by the SRS-2 and Vineland-3, necessitate targeted interventions to improve these skills. Her challenges in understanding social cues and maintaining conversations impact her ability to form relationships.
- Emotional Regulation: The GARS-3 Emotional Responses score of 4 and GAD-7 score of 18 reflect challenges in managing emotional responses and anxiety, impacting her social and occupational functioning. These difficulties contribute to her experiences of stress and frustration in social situations.

XI. Risk and Protective Factors
Risk Factors:

1. High Anxiety Levels: Sophie's GAD-7 score of 18 indicates severe anxiety, which can exacerbate social and adaptive challenges, impacting her ability to function effectively in daily life.
2. Emotional Dysregulation: The GARS-3 Emotional Responses score suggests significant difficulties in managing emotional states, which can lead to stress and frustration in social and occupational settings.
3. Familial Stressors: A family history of emotional problems and current familial discord may negatively influence Sophie's mental health and overall prognosis, contributing to her anxiety and depressive symptoms.

Protective Factors:

1. Cognitive Strengths: Sophie's nonverbal IQ score of 106 highlights strengths in visual-spatial reasoning and pattern recognition, which can be leveraged in structured learning and problem-solving tasks.
2. Supportive Relationships: Her reliance on a few deep connections provides emotional support and stability, serving as a buffer against stress and promoting resilience.
3. Intense Interests: Her strong cognitive style and focused interests can be harnessed to engage her in meaningful activities, fostering a sense of competence and achievement.

{all_text_combined}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating DSM-5 Criteria Analysis, Strengths and Challenges, and Risk and Protective Factors sections of a Psychological Assessment Report based on provided information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_sections_12_14(previous_sections_text):
    prompt = f"""
Based on the following sections of the report, generate Sections XII, XIII, and XIV of the Psychological Assessment Report.

XII. Recommendations
- Provide specific, actionable recommendations for interventions.
- Include therapies, support services, and strategies.

XIII. Prognosis
- Discuss the patient's prognosis with and without intervention.
- Consider risk and protective factors.

XIV. Follow-Up Plan
- Outline goals, objectives, and strategies.
- Include timelines for re-evaluation.

Use professional language and ensure the content aligns with the structure provided.

This is a simulated perfect response for this section:

XII. Recommendations 
1. Speech Therapy: Focus on improving verbal communication and social interaction skills, targeting specific areas such as turn-taking and understanding non-verbal cues.
2. Occupational Therapy: Assist with sensory processing and motor skills to enhance daily functioning, addressing sensory sensitivities and improving coordination and self-care skills. 
3. Applied Behavior Analysis (ABA): Address repetitive behaviors and develop adaptive coping strategies, reducing stereotyped actions and promoting more flexible behavior patterns. 
4. Cognitive-Behavioral Therapy (CBT): Target anxiety and emotional regulation to improve overall well-being, providing strategies for managing stress and reducing anxiety symptoms. 
5. Social Skills Training: Enhance social communication and interaction abilities through structured programs, focusing on building confidence and competence in social settings. 

XIII. Prognosis
With intervention, Sophie is likely to experience improvements in social communication, emotional regulation, and adaptive functioning. Her cognitive strengths and supportive relationships can facilitate progress and enhance her quality of life. Without intervention, challenges in these areas may persist, impacting her social integration and overall well-being. The presence of risk factors, such as anxiety and familial stressors, may further complicate her prognosis without targeted support. 

XIV. Follow-Up Plan
Goals:
Improve Social Communication:
Objective: Achieve measurable progress in social interaction skills within six months, with re-evaluation to assess effectiveness.
Strategies:
- Social Skills Training: Enroll Sophie in an adult-focused social skills training course that addresses practical conversational skills, interpreting social cues, and effective ways to initiate and maintain social interactions. The course should involve real-life scenarios relevant to adults, such as workplace interactions and social gatherings.
- Peer Mentorship Program: Pair Sophie with an adult peer mentor who has successfully navigated similar social communication challenges. The mentor will model appropriate social behaviors, provide feedback on Sophie's interactions, and offer guidance on nuanced social strategies suitable for adults.
- Structured Social Activities: Facilitate Sophie's participation in structured social activities tailored to adults, such as book clubs, community service groups, or adult education classes. These environments provide predictable social contexts where Sophie can practice her communication skills.

Enhance Emotional Regulation:
Objective: Reduce anxiety symptoms and improve coping strategies through CBT, with progress monitored quarterly.
Strategies:
- Adult Anxiety Management Group: Enroll Sophie in a support group for adults with anxiety where she can share experiences and learn from others dealing with similar issues. Group sessions will focus on adult-specific stressors such as workplace anxiety and managing family relationships.
- Mindfulness and Relaxation Techniques: Introduce Sophie to mindfulness practices and relaxation techniques that are suitable for adults, such as deep breathing exercises, progressive muscle relaxation, and guided imagery. Sophie will have individual sessions with a therapist to practice these techniques.
- Biofeedback Therapy: Introduce biofeedback therapy sessions tailored to adults to help Sophie gain awareness and control over physiological responses to stress. This can help her develop better self-regulation techniques for managing anxiety.

Develop Adaptive Skills:
Objective: Increase independence in daily living tasks through occupational therapy, with biannual assessments to track growth.
Strategies:
- Occupational Therapy for Adults: Schedule bi-weekly sessions with an occupational therapist who specializes in working with adults. The therapy will focus on enhancing Sophie's skills in managing finances, preparing meals, and navigating community resources independently.
- Life Skills Workshops: Enroll Sophie in monthly life skills workshops specifically designed for adults. These workshops will cover topics such as budgeting, job interviewing, and advanced cooking techniques, providing hands-on experience in essential adult life skills.
- Sensory-Friendly Home Adjustments: Collaborate with an occupational therapist to identify and implement sensory-friendly modifications in Sophie's home environment. These modifications may include lighting adjustments, organization systems, and designated quiet zones to optimize her daily living space.

Additional Supportive Elements:
- Regular Multi-Disciplinary Review: Establish a multi-disciplinary team including her therapist, occupational therapist, primary care physician, and a vocational counselor. Quarterly meetings will be held to review Sophie's progress, adjust her intervention plan, and ensure a cohesive approach.
- Parental and Spousal Involvement: Encourage involvement from Sophie's husband in her therapeutic activities. Regularly scheduled joint sessions can help him understand her challenges and ways to effectively support her, enhancing the overall family dynamic and ensuring a consistent approach.
- Accessible and Inclusive Activities: Identify and facilitate participation in community activities that are inclusive and understanding of individuals with ASD. Such activities could include ASD-friendly social clubs, volunteer opportunities, and hobby groups that align with Sophie's interests, providing her with low-pressure environments to practice her social skills.

Previous Sections:
{previous_sections_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with generating Recommendations, Prognosis, and Follow-Up Plan sections of a Psychological Assessment Report based on previous sections."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content

def generate_section_15(previous_sections_text):
    prompt = f"""
Based on the following sections of the report, generate Section XV (Interpretative Summary) of the Psychological Assessment Report. Provide:

- A concise summary of findings.
- Highlight key strengths and challenges.
- Summarize recommendations.

Use professional language and ensure the content aligns with the structure provided.

This is a simulated perfect response for this section:
XV. Interpretative Summary
Sophie presents a complex profile characterized by significant challenges in social communication, emotional regulation, and adaptive functioning, consistent with Autism Spectrum Disorder (ASD) and Generalized Anxiety Disorder (GAD). The assessments, including the GARS-3, SRS-2, Vineland-3, and RAADS-R, highlight persistent deficits in social interaction and communication, alongside restricted and repetitive behaviors. These findings align with DSM-5 criteria for ASD, underscoring the need for substantial support. 

Key strengths include Sophie's cognitive abilities, particularly in visual-spatial reasoning, and her intense interests, which can be leveraged to engage her in meaningful activities. However, her high levels of anxiety and emotional dysregulation, compounded by familial stressors, pose significant risk factors that may impact her prognosis. To address these challenges, a comprehensive intervention plan is recommended, prioritizing speech therapy to enhance verbal communication, occupational therapy to assist with sensory processing and motor skills, and Applied Behavior Analysis (ABA) to address repetitive behaviors. Cognitive-Behavioral Therapy (CBT) is advised to target anxiety and emotional regulation, while social skills training can improve her social interaction abilities. 

The follow-up plan includes specific goals to improve social communication, enhance emotional regulation, and develop adaptive skills, with timelines for re-evaluation to monitor progress. With targeted interventions and support, Sophie is likely to experience improvements in her quality of life and social integration, leveraging her strengths to overcome challenges and achieve greater independence. 

Previous Sections:
{previous_sections_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with summarizing a Psychological Assessment Report based on previous sections."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    return response.choices[0].message.content

def generate_section_16(all_texts, previous_sections_text):
    all_text_combined = '\n\n'.join([f"{key}:\n{value}" for key, value in all_texts.items()])
    prompt = f"""
Based on all the information from the files and the previous sections of the report, generate Section XVI (Diagnosis and Resources) of the Psychological Assessment Report.

- Provide the primary and secondary diagnoses with justification based on DSM-5 criteria.
- List resources for the patient, including local services, support groups, and therapy options.

Use professional language and ensure the content aligns with the structure provided.

This is a simulated perfect response for this section:

XVIII. Diagnosis 

XVIII. Diagnosis

Primary Diagnosis:

Autism Spectrum Disorder, Level 2

Autism Spectrum Disorder (ASD) Level 2 is a significant developmental condition characterized by substantial deficits in social communication and social interaction, alongside restricted, repetitive patterns of behavior, interests, or activities. Sophie's comprehensive evaluation unequivocally indicates the presence of ASD, substantiated by multiple robust assessment measures and thorough clinical observations.

Persistent Deficits in Social Communication and Social Interaction:

Social Communication: Sophie's GARS-3 score of 6 in Social Communication and SRS-2 T-score of 54 reveal pronounced challenges in reciprocal conversation and social understanding. Clinical observations during therapy sessions noted her proclivity for tangential speech and difficulty in interpreting social cues. For instance, Sophie often misinterprets figurative language and struggles to maintain conversational flow, frequently diverging off-topic. This aligns with DSM-5 criteria for deficits in social-emotional reciprocity, which manifest as impaired back-and-forth conversation and reduced sharing of interests, emotions, or affect. These deficits impede her ability to form and sustain meaningful conversational exchanges, thereby hampering her social connectivity.

Social Interaction: Sophie's RAADS-R score of 50 in Social Relatedness and Vineland-3 Socialization score of 69 underscore significant difficulties in forming and maintaining social relationships. Clinical assessments reveal that Sophie prefers solitary activities and exhibits considerable discomfort in group settings. Her interactions are typically confined to close relationships, primarily with family members and her husband, reflecting profound challenges in developing and maintaining broader social networks. This behavior is consistent with DSM-5 criteria for deficits in developing, maintaining, and understanding relationships, characterized by a lack of interest in peers and difficulty adjusting behavior to suit diverse social contexts.

Restricted, Repetitive Patterns of Behavior, Interests, or Activities:

Repetitive Behaviors: The GARS-3 score of 8 in Restricted/Repetitive Behaviors and SRS-2 T-score of 50 in Restricted Interests and Repetitive Behavior indicate the presence of stereotyped actions and restricted interests. Behavioral observations and self-reports document Sophie's hyperfixation on singing and spiritual topics, where she engages in these activities for prolonged periods without dwindling interest. Additionally, her stimming behaviors, such as biting the skin off her fingertips and historically leg bouncing, were evident during interactions. These behaviors align with DSM-5 criteria for stereotyped or repetitive motor movements, use of objects, or speech, as well as an insistence on sameness and inflexible adherence to routines. These repetitive patterns significantly impact her daily functioning, necessitating structured interventions to manage and potentially mitigate their effects.

Symptoms Present in Early Developmental Period:

Sophie's developmental history substantiates the early presence of ASD symptoms. Detailed parental reports and early childhood records highlight delayed milestones in social engagement and a marked preference for solitary play. Such early signs include extensive solitary singing and limited interest in interactive play with peers, consistently evident from a young age. These early developmental signs align with DSM-5 criteria, stipulating the presence of symptoms during the early developmental period, thereby confirming a longstanding developmental trajectory consistent with ASD.

Symptoms Cause Clinically Significant Impairment:

The impact of ASD symptoms on Sophie's daily functioning is profound. Her difficulties in social integration, communication, and emotional regulation are evident across multiple assessments. For example, Sophie reports significant challenges in maintaining employment due to frequent miscommunications with colleagues and overwhelming stress in social work environments. Furthermore, her considerable anxiety in social situations has led to an isolated lifestyle, exacerbating her mental health issues. These behaviors meet DSM-5 criteria for clinically significant impairment in social, occupational, or other crucial areas of functioning, emphasizing the necessity for substantial support and intervention.
Secondary Diagnosis:
Generalized Anxiety Disorder (GAD)

In addition to ASD, Sophie's diagnostic profile is characterized by Generalized Anxiety Disorder (GAD), as evidenced by her GAD-7 score of 18. This indicates severe anxiety, manifesting as pervasive nervousness, restlessness, and an inability to relax. These anxiety symptoms significantly contribute to and exacerbate her social and adaptive functioning challenges, warranting integrated therapeutic approaches to address both ASD and anxiety concurrently.

In summary, Sophie Betten's diagnostic evaluation reveals compelling evidence of Autism Spectrum Disorder, Level 2, underpinned by persistent deficits in social communication and interaction, coupled with restricted and repetitive behaviors. These findings are corroborated by multiple standardized assessments and clinical observations, underscoring the necessity for a comprehensive, multi-disciplinary intervention strategy. Further evaluations to explore comorbid conditions and a tailored treatment plan targeting both ASD and GAD are crucial for enhancing Sophie's overall well-being and functional autonomy.
XVIV. Resources 

Wesley Family Services - Autism Center
Location: Bridgeville, PA (5 miles)
Reason for Referral: They offer autism services, including individualized behavior plans and social skills training tailored to adults with ASD.
Achieva Autism Services
Location: Pittsburgh, PA (12 miles)
Reason for Referral: Provides resources for adults with ASD, including vocational training, support services, and social programs.
Carnegie Autism Behavioral Health
Location: Carnegie, PA (8 miles)
Reason for Referral: Offers ABA therapy and other behavioral health services that are tailored for adults with ASD, helping them with social and behavioral skills.
Alliance Health Wraparound Services
Location: Bethel Park, PA (3 miles)
Reason for Referral: Focuses on mental health and developmental disabilities, offering individualized services for ASD adults.
Southwestern Pennsylvania Human Services (SPHS)
Location: Washington, PA (13 miles)
Reason for Referral: Offers a range of services, including community-based programs for adults with developmental disabilities like ASD.
The Watson Institute
Location: Bridgeville, PA (5 miles)
Reason for Referral: Offers specialized programs, including social skills training and educational support for adults on the spectrum.
Autism Connection of Pennsylvania
Location: Pittsburgh, PA (12 miles)
Reason for Referral: Provides various services including social groups, educational resources, and support services for adults with ASD.
Milestone Centers, Inc.
Location: Monroeville, PA (15 miles)
Reason for Referral: Offers services such as individual therapy and group programs designed to support adults with autism.
Spectrum Charter School
Location: Monroeville, PA (14 miles)
Reason for Referral: Focuses on ASD services, including vocational training, life skills, and personalized education plans for adults.
Pressley Ridge Autism Services
Location: Pittsburgh, PA (12 miles)
Reason for Referral: Provides comprehensive care, including ABA therapy, life skills coaching, and job readiness programs for adults with ASD.


All Files Text:
{all_text_combined}

Previous Sections:
{previous_sections_text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a highly skilled psychologist tasked with providing the Diagnosis and Resources sections of a Psychological Assessment Report based on all provided information."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return response.choices[0].message.content


@shared_task(name='adult_report_generator.generate_full_report')
def generate_full_report(session_id, s3_paths, user_output_folder, aws_access_key_id, aws_secret_access_key, aws_default_region, s3_bucket):
    logger.info(f"Starting report generation for session {session_id}")
    
    try:
        # Create S3 client
        s3_client = get_s3_client(aws_access_key_id, aws_secret_access_key, aws_default_region)
        
        logger.info("Downloading and extracting text from S3 files")
        all_texts = {}

        # Download and extract text from all files directly from S3
        for filename, s3_key in s3_paths.items():
            logger.info(f"Processing file: {filename}")
            try:
                file_content = download_file_from_s3_to_memory(
                    s3_key,
                    aws_access_key_id,
                    aws_secret_access_key,
                    aws_default_region,
                    s3_bucket
                )
                if file_content:
                    file_name = os.path.basename(filename)
                    all_texts[file_name.split('.')[0]] = extract_text_from_pdf_bytes(file_content)
                else:
                    raise Exception(f"Failed to download file from S3: {s3_key}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                raise

        # Assign specific texts to variables
        transcript_text = all_texts.get('Transcript', '')
        intakeform_text = all_texts.get('IntakeForm_Results', '')

        # Generate report sections
        generated_sections = {}
        logger.info("Generating report sections")
        markdown_content = ""
        
        # Define and generate all sections
        sections = [
            ('sections_1_3', generate_sections_1_3(intakeform_text, transcript_text)),
            ('section_4', generate_section_4(intakeform_text, transcript_text)),
            ('section_5', generate_section_5(all_texts)),
            ('sections_6_7', generate_sections_6_7(intakeform_text, transcript_text)),
            ('section_8', generate_section_8(all_texts)),
            ('sections_9_11', generate_sections_9_11(all_texts)),
        ]

        for section_name, content in sections:
            logger.info(f"Generating section: {section_name}")
            generated_sections[section_name] = content
            markdown_content += content + "\n\n"

        # Generate remaining sections
        previous_sections_text = '\n\n'.join(generated_sections.values())
        remaining_sections = [
            ('sections_12_14', generate_sections_12_14(previous_sections_text)),
            ('section_15', generate_section_15(previous_sections_text)),
            ('section_16', generate_section_16(all_texts, previous_sections_text)),
        ]

        for section_name, content in remaining_sections:
            logger.info(f"Generating section: {section_name}")
            generated_sections[section_name] = content
            markdown_content += content + "\n\n"

        logger.info("Generating PDFs")
        # Generate cover page and table of contents
        cover_content = generate_cover_page()
        toc_content = generate_table_of_contents()
        
        # Use the updated simple_markdown_to_pdf function
        main_content_pdf = simple_markdown_to_pdf(cover_content, toc_content, markdown_content)

        logger.info("PDF generation completed")

        # Upload the PDF to S3
        s3_report_path = f'{session_id}/generated_par.pdf'
        if upload_bytes_to_s3(
            main_content_pdf,
            s3_report_path,
            aws_access_key_id,
            aws_secret_access_key,
            aws_default_region,
            s3_bucket
        ):
            logger.info(f"Report generation completed and uploaded for session {session_id}")
            return {'status': 'success', 's3_path': s3_report_path}
        else:
            logger.error(f"Failed to upload generated report to S3 for session {session_id}")
            raise Exception("Failed to upload generated report to S3")

    except Exception as e:
        logger.error(f"An error occurred during report generation: {e}")
        return {'status': 'error', 'message': str(e)}