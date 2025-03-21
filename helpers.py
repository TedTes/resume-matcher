import requests
import spacy
import re
from collections import Counter
from datetime import datetime
def fetch_jobs(search_term=None, location=None, remote=None):
    """
    Fetch jobs from the Arbeitnow API with optional filters
    """
    url = "https://www.arbeitnow.com/api/job-board-api"
    params = {}
    
    if search_term:
        params['search'] = search_term
    if location:
        params['location'] = location
    if remote is not None:
        params['remote'] = 'true' if remote else 'false'
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return []

def fetch_job_by_slug(slug):
    """
    Fetch a specific job from the Arbeitnow API using its slug
    """
    url = "https://www.arbeitnow.com/api/job-board-api"
    
   
    params = {'slug': slug}
    
    try:
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        matching_job = next((job for job in data if job.get('slug') == slug), None)
        if matching_job:
            return matching_job
        # If the API doesn't support slug filtering, we need to fetch all and filter
        if not data or len(data) > 1:
            print("API doesn't support direct slug lookup, fetching all jobs")
            all_jobs = fetch_jobs()
            return next((job for job in all_jobs if job.get('slug') == slug), None)
            
        return None
    except requests.RequestException as e:
        print(f"API request error when fetching job by slug: {e}")
        return None


def analyze_job_description(description):
    """
    Analyze job description to extract important skills and keywords
    This is a simplified version -  TODO: use more 
     NLP techniques with spaCy
    """
    # List of common technology skills to look for
    tech_skills = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "Agile", "Scrum",
        "Frontend", "Backend", "Full Stack", "Web", "Mobile", "Android", "iOS",
        "Machine Learning", "AI", "Data Science", "Big Data", "Cloud", "API"
    ]
    
    # List of common soft skills
    soft_skills = [
        "Communication", "Teamwork", "Leadership", "Problem Solving", 
        "Critical Thinking", "Time Management", "Adaptability", 
        "Creativity", "Attention to Detail", "Customer Service",
        "Presentation", "Negotiation", "Conflict Resolution"
    ]
    
    # Combine all skills
    all_skills = tech_skills + soft_skills
    
    # Find matching skills in description (case-insensitive)
    description_lower = description.lower()
    found_skills = []
    
    for skill in all_skills:
        if skill.lower() in description_lower:
            found_skills.append(skill)
    
    return found_skills

def extract_job_tags(title, description):
    """
    Extract relevant tags from job title and description
    """
    # List of common technology keywords to look for
    tech_keywords = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "Agile", "Scrum",
        "Frontend", "Backend", "Full Stack", "Web", "Mobile", "Android", "iOS",
        "Machine Learning", "AI", "Data Science", "Big Data", "Cloud", "API"
    ]
    
    # Combine title and description, lowercase for case-insensitive matching
    text = f"{title} {description}".lower()
    
    # Find matching tags
    tags = []
    for keyword in tech_keywords:
        if keyword.lower() in text:
            tags.append(keyword)
    
    # Check for remote work
    if "remote" in text or "work from home" in text:
        tags.append("Remote")
    
    # Check for job types
    job_types = ["Full-time", "Part-time", "Contract", "Freelance", "Internship"]
    for job_type in job_types:
        if job_type.lower() in text:
            tags.append(job_type)
    
    return tags
# from weasyprint import HTML
def generate_pdf(html_string):
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    return pdf


def calculate_resume_completeness(resume_data):
    """
    Calculate completeness percentage of a resume based on filled sections
    """
    if not resume_data:
        return 0
        
    # Define key sections for a complete resume
    key_sections = ['contact', 'summary', 'experience', 'education', 'skills']
    
    # Count completed sections
    completed = sum(1 for section in key_sections if section in resume_data and resume_data[section])
    
    # Calculate percentage
    return int((completed / len(key_sections)) * 100)


def extract_skills_from_text(text):
    """
    Extract skills from text using NLP techniques.
    Returns a dictionary of skills with their importance score.
    """
    # Load the spaCy model
    nlp = spacy.load('en_core_web_sm')
    # Common technical skills to look for
    tech_skills = [
        "Python", "JavaScript", "React", "Angular", "Vue", "Node.js", "Django", 
        "Flask", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "AWS", "Azure", 
        "GCP", "Docker", "Kubernetes", "DevOps", "CI/CD", "Git", "GitHub", "GitLab",
        "Agile", "Scrum", "Kanban", "REST", "GraphQL", "API", "Microservices",
        "HTML", "CSS", "SASS", "LESS", "Bootstrap", "Tailwind", "TypeScript",
        "Java", "C#", "C++", "Ruby", "PHP", "Go", "Rust", "Swift", "Kotlin",
        "Redux", "jQuery", "Express", "Spring", "Laravel", "Rails", "ASP.NET",
        "TDD", "BDD", "Machine Learning", "AI", "Data Science", "Big Data", 
        "Hadoop", "Spark", "Kafka", "ElasticSearch", "Tableau", "Power BI",
        "Linux", "Unix", "Windows", "MacOS", "Mobile", "Android", "iOS",
        "Responsive Design", "Webpack", "Babel", "Gulp", "Grunt", "npm", "yarn",
        "SEO", "Accessibility", "WCAG", "Performance Optimization", "Security",
        "Frontend", "Backend", "Full Stack", "UI/UX", "Figma", "Sketch", "Adobe XD"
    ]
    
    # Common soft skills
    soft_skills = [
        "Communication", "Teamwork", "Leadership", "Problem Solving", 
        "Critical Thinking", "Time Management", "Project Management", 
        "Adaptability", "Creativity", "Attention to Detail", "Analytical",
        "Interpersonal", "Presentation", "Negotiation", "Conflict Resolution",
        "Decision Making", "Emotional Intelligence", "Customer Service", 
        "Multitasking", "Flexibility", "Initiative", "Self-Motivation"
    ]
    
    # Combine all skills
    all_skills = tech_skills + soft_skills
    skill_patterns = {skill.lower(): skill for skill in all_skills}
    
    # Process the text
    doc = nlp(text)
    
    # Extract skills using multiple approaches
    found_skills = {}
    
    # 1. Direct matching of skill keywords
    for token in doc:
        token_lower = token.text.lower()
        if token_lower in skill_patterns:
            actual_skill = skill_patterns[token_lower]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 1
    
    # 2. Look for compound skills (e.g., "machine learning")
    for i in range(len(doc) - 1):
        bigram = (doc[i].text + " " + doc[i+1].text).lower()
        if bigram in skill_patterns:
            actual_skill = skill_patterns[bigram]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 2  # Higher score for compounds
    
    # 3. Analyze using noun chunks (might find things like "data analysis")
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower()
        if chunk_text in skill_patterns:
            actual_skill = skill_patterns[chunk_text]
            found_skills[actual_skill] = found_skills.get(actual_skill, 0) + 2
    
    # 4. Look for skills near requirement words
    requirement_indicators = ["required", "requirements", "qualifications", "skills", "proficiency", "knowledge", "experience with"]
    requirement_section = False
    skill_context_bonus = {}
    
    for sent in doc.sents:
        sent_text = sent.text.lower()
        
        # Check if this is a requirements section
        if any(indicator in sent_text for indicator in requirement_indicators):
            requirement_section = True
        
        if requirement_section:
            # Skills mentioned in requirements sections get a bonus
            for skill, original in skill_patterns.items():
                if skill in sent_text:
                    skill_context_bonus[original] = skill_context_bonus.get(original, 0) + 3
    
    # Add the context bonuses to the found skills
    for skill, bonus in skill_context_bonus.items():
        found_skills[skill] = found_skills.get(skill, 0) + bonus
    
    # Convert counts to importance scores (0-100)
    total_mentions = sum(found_skills.values()) if found_skills else 1
    skill_scores = {}
    
    for skill, count in found_skills.items():
        # Calculate normalized score (0-100)
        normalized_score = min(100, int((count / total_mentions) * 100) + 50)
        skill_scores[skill] = normalized_score
    
    return skill_scores




def calculate_skill_match(user_skills, job_skills):
    """
    Calculate the match percentage between user skills and job skills.
    
    Parameters:
    - user_skills: List of strings representing user's skills
    - job_skills: Dictionary of job skills with importance scores
    
    Returns:
    - match_percentage: Overall match percentage (0-100)
    - skill_matches: List of dictionaries with skill match details
    """
    if not user_skills or not job_skills:
        return 0, []
    
    # Normalize user skills (convert to lowercase for matching)
    user_skills_normalized = [skill.lower() for skill in user_skills]
    
    # Initialize match metrics
    total_job_importance = sum(job_skills.values())
    total_match_score = 0
    skill_matches = []
    
    # Calculate match for each job skill
    for job_skill, importance in job_skills.items():
        skill_match = 0
        
        # Exact match
        if job_skill.lower() in user_skills_normalized:
            skill_match = 100
        else:
            # Check for partial matches (e.g., "Python" would partially match "Python Programming")
            for user_skill in user_skills_normalized:
                if job_skill.lower() in user_skill or user_skill in job_skill.lower():
                    # Partial match - score based on similarity
                    skill_match = 70
                    break
        
        # Add to skill matches list
        if skill_match > 0:
            skill_matches.append({
                "name": job_skill,
                "match": skill_match,
                "importance": importance
            })
            
            # Add to total match score, weighted by importance
            total_match_score += (skill_match / 100) * importance
    
    # Calculate overall match percentage
    if total_job_importance > 0:
        overall_match = int((total_match_score / total_job_importance) * 100)
    else:
        overall_match = 0
    
    # Sort skills by importance
    skill_matches.sort(key=lambda x: x["importance"], reverse=True)
    
    # Limit to top skills
    skill_matches = skill_matches[:10]
    
    return overall_match, skill_matches



def find_similar_jobs(current_slug, job_skills, limit=3):
    """
    Find similar jobs based on skills overlap
    """
    from models import Job
    
    try:
        # Get all jobs except the current one
        all_jobs = Job.query.filter(Job.slug != current_slug).all()
        job_scores = []
        
        for job in all_jobs:
            # Extract skills from this job
            other_job_skills = extract_skills_from_text(job.description)
            
            # Calculate similarity score based on skills overlap
            similarity_score = 0
            
            for skill, importance in job_skills.items():
                if skill in other_job_skills:
                    # Add to similarity score, weighted by both jobs' importance for this skill
                    other_importance = other_job_skills.get(skill, 0)
                    similarity_score += (importance + other_importance) / 2
            
            # Add location score if locations match
            current_job = Job.query.filter_by(slug=current_slug).first()
            if current_job and job.location == current_job.location:
                similarity_score += 20
            
            # Add to scores list
            job_scores.append((similarity_score, job))
        
        # Sort by score (highest first) and take top X
        job_scores.sort(reverse=True, key=lambda x: x[0])
        similar_jobs = [job for _, job in job_scores[:limit]]
        
        # Process similar jobs for display (add any needed attributes)
        for job in similar_jobs:
            # Add tags for display
            job.tags = list(extract_skills_from_text(job.description).keys())[:5]
            
            # Format dates
            days_ago = (datetime.now() - job.posted_at).days if job.posted_at else 0
            if days_ago == 0:
                job.created_at = "Today"
            elif days_ago == 1:
                job.created_at = "Yesterday"
            else:
                job.created_at = f"{days_ago} days ago"
        
        return similar_jobs
    
    except Exception as e:
        print(f"Error finding similar jobs: {e}")
        return []
    



def get_recent_job_matches(user_id, limit=3):
    """
    Fetch recent job matches from the database for a specific user.
    
    Args:
        user_id: The ID of the user to fetch matches for
        limit: Maximum number of matches to return
        
    Returns:
        A list of job match dictionaries
    """
    from models import Job, Resume
    from sqlalchemy import desc
    
    try:
        # Get the user's skills from their most recent resume
        user_resume = Resume.query.filter_by(user_id=user_id).order_by(desc(Resume.updated_at)).first()
        if not user_resume or not user_resume.resume_data or 'skills' not in user_resume.resume_data:
            # If no skills found, return the most recent jobs posted
            recent_jobs = Job.query.order_by(desc(Job.posted_at)).limit(limit).all()
            return [{
                'slug': job.slug,
                'title': job.title,
                'company_name': job.company,
                'location': job.location,
                'remote': 'remote' in job.location.lower() if job.location else False,
                'created_at': (datetime.now() - job.posted_at).days if job.posted_at else 0,
                'match': 50  # Default match score of 50% for users without skills
            } for job in recent_jobs]
        
        # Extract user skills
        user_skills_data = user_resume.resume_data['skills']
        user_skills = []
        
        if isinstance(user_skills_data, str):
            user_skills = [skill.strip() for skill in user_skills_data.split(',')]
        elif isinstance(user_skills_data, list):
            user_skills = user_skills_data
        
        # Get all jobs to match against
        all_jobs = Job.query.order_by(desc(Job.posted_at)).limit(50).all()
        # Calculate match score for each job
        job_matches = []
        
        for job in all_jobs:
            # Extract skills from job description
            job_skills = extract_skills_from_text(job.description)
            
            # Calculate match score
            match_percentage, _ = calculate_skill_match(user_skills, job_skills)
            
            # Create job match dictionary with score
            job_match = {
                'id': job.id,
                'slug': job.slug,
                'title': job.title,
                'company_name': job.company,
                'location': job.location,
                'remote': 'remote' in job.location.lower() if job.location else False,
                'match': match_percentage,
                'created_at': (datetime.now() - job.posted_at).days if job.posted_at else 0
            }
            
            job_matches.append(job_match)
        
        # Sort by match score (highest first) and take top matches
        job_matches.sort(key=lambda x: x['match'], reverse=True)
        
        return job_matches[:limit]
    
    except Exception as e:
        print(f"Error getting job matches: {e}")
        import traceback
        traceback.print_exc()
        return []