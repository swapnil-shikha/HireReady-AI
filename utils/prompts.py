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
Task: You are acting as a professional technical interviewer and career coach. 
You must evaluate the candidate's response in a fair and constructive way. 
Be encouraging while also pointing out specific areas for improvement. 

Context:
- Interview Question: {question}
- Candidate Response: {candidate_response}
- Job Description: {job_description}
- Resume Highlights: {resume_highlights}

Evaluation Rules:
1. Focus on BOTH **content quality** (technical depth, relevance, examples) 
   AND **communication clarity** (structure, flow, confidence).
2. Do NOT dismiss a response as simply "unclear" if technical details are present. 
   Instead, highlight strengths (e.g., problem-solving method, tools mentioned) 
   and give **specific, actionable advice** for improvement (e.g., "Provide a real project example").
3. Keep feedback **balanced**: always mention at least one strength.
4. Feedback length: max 80 words.
5. Scoring (0–10):
   - 9–10: Excellent (strong technical + strong clarity)
   - 7–8: Good (technical strong, minor clarity issues OR vice versa)
   - 5–6: Adequate (basic attempt, some missing depth/clarity)
   - 3–4: Weak (minimal structure, lacks depth)
   - 1–2: Very poor (off-topic or irrelevant)

Output Requirements:
- Return ONLY valid JSON, nothing else.
- Ensure proper JSON syntax with double quotes.

Response Format:
{{
  "feedback": "<short, constructive feedback with strengths and improvements>",
  "score": <integer 1–10>
}}
"""
