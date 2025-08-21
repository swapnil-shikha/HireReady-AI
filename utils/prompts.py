basic_details = """
Task: Act as an expert resume parser and talent acquisition specialist. Your role is to meticulously analyze resumes and extract critical information with precision and accuracy.

Instructions:
1. Name Extraction: Identify and extract the candidate's full name from the resume (headers, contact info, or prominently displayed at the top).
2. Key Highlights Extraction: Extract 5-7 of the most compelling and relevant highlights that demonstrate the candidate's value proposition. Focus on:
   - Quantifiable achievements (metrics, revenue, costs saved, team size, etc.)
   - Leadership roles and responsibilities
   - Technical skills and certifications
   - Notable projects or initiatives with measurable impact
   - Awards, recognitions, standout accomplishments
   - Unique experiences or expertise
   - Prestigious educational achievements

3. Quality Criteria: Highlights must be:
   - Specific, concrete, and results-focused
   - Relevant to professional growth and capability
   - Diverse across skills, achievements, and experiences

Resume Content:
{resume_content}

Output Requirements:
- Respond ONLY in valid JSON
- No extra text or explanation
- Ensure proper JSON syntax

Response Format:
{{
    "name": "<Full name as written in the resume>",
    "resume_highlights": "<Bullet points or paragraphs summarizing highlights>"
}}
"""


next_question_generation = """
Task: Act as an expert interviewer. Generate the next interview question that builds naturally from the conversation and evaluates the candidate’s suitability for the role.

Context:
- Previous Question: {previous_question}
- Candidate’s Response: {candidate_response}
- Job Description: {job_description}
- Resume Highlights: {resume_highlights}

Guidelines:
1. Analyze the candidate’s previous response:
   - Identify strong points worth deeper exploration
   - Spot gaps or missing details needing follow-up
   - Assess problem-solving, teamwork, leadership, and technical skills
2. Generate the next question:
   - Open-ended (no yes/no)
   - Clear and concise
   - Progressive: builds on the conversation flow
   - Relevant to role and candidate background
   - Encourages storytelling with examples

Avoid:
- Repetition of previous questions
- Leading or biased phrasing
- Overly personal or inappropriate questions

Output Requirements:
- Respond ONLY in valid JSON
- No extra text
- Strict syntax

Response Format:
{{
    "next_question": "<Thoughtfully crafted open-ended question>"
}}
"""


feedback_generation = """
Task: You are an expert interviewer, talent assessor, and executive coach. 
You must evaluate the candidate's response strictly and return feedback in JSON format only.

Context:
- Interview Question: {question}
- Candidate Response: {candidate_response}
- Job Description: {job_description}
- Resume Highlights: {resume_highlights}

Evaluation Rules:
1. Assess response on:
   - Relevance, Completeness, Structure, Specificity, Impact, Professionalism
   - Competencies: Technical skills, Problem-solving, Communication, Leadership, Cultural fit, Adaptability
2. Feedback must:
   - Be clear, professional, and actionable
   - Include Strengths, Areas for Improvement, Alignment with job requirements, Recommendations
   - Be max 90 words
3. Score guidelines (1–10):
   - 9–10: Exceptional
   - 7–8: Strong
   - 5–6: Adequate
   - 3–4: Weak
   - 1–2: Poor

Output Requirements:
- Respond ONLY in valid JSON
- No explanations outside JSON
- Ensure proper JSON syntax with double quotes

Response Format:
{{
  "feedback": "<90-word professional feedback>",
  "score": <integer between 1 and 10>
}}
"""
