from flask import make_response,render_template, request, redirect, url_for, flash, session, abort, send_file
from helpers import fetch_jobs,extract_job_tags,calculate_resume_completeness,extract_skills_from_text,find_similar_jobs,calculate_skill_match,analyze_job_description
from flask import render_template, request, redirect, url_for, flash, session, abort, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io
from sqlalchemy.orm import attributes
from forms import RegistrationForm, LoginForm, JobSearchForm, ContactForm, SummaryForm, ExperienceForm, EducationForm, SkillsForm
from db import db
from models import  User, Job, Resume
import json
from flask import jsonify

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from io import BytesIO
# Import NLP analyzer 
import spacy
nlp = spacy.load('en_core_web_sm')

app = None

def init_routes(flask_app):
    global app
    app = flask_app
    @app.route('/')
    def home():
        try:
            job_count = Job.query.count()
            user_count = User.query.count()
            resume_count = Resume.query.count()
            return render_template('home.html', job_count=job_count, user_count=user_count, resume_count=resume_count)
        except Exception as e:
             print(f"Error rendering home page: {e}")  # Debug print
             abort(500)

    @app.route('/jobs', methods=['GET', 'POST'])
    def jobs():
        form = JobSearchForm()
        jobs_data = []
        
        try:
            if form.validate_on_submit():
                # Get form data for filtering
                search_term = form.search.data
                location = form.location.data
                remote_only = form.remote.data
                
                # Fetch jobs with filters
                jobs_data = fetch_jobs(search_term, location, remote_only)
            else:
                # Default fetch with no filters
                jobs_data = fetch_jobs()

            # Process job data to extract tags and format dates
            processed_jobs = []
            for job in jobs_data:
                # Extract tags from job title and description
                tags = extract_job_tags(job.get('title', ''), job.get('description', ''))
                
                # Format the date
                created_at = job.get('created_at')
                if created_at:
                    # Convert ISO date to more readable format
                    try:
                        if created_at and isinstance(created_at,str):
                           date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            date_obj = datetime.now()
                        days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                        
                        if days_ago == 0:
                            formatted_date = "Today"
                        elif days_ago == 1:
                            formatted_date = "Yesterday"
                        else:
                            formatted_date = f"{days_ago} days ago"
                    except:
                        formatted_date = "Recently"
                else:
                    formatted_date = "Recently"
                
                # Create processed job object
                processed_job = {
                    **job,  # Include all original job data
                    'tags': tags[:3],  # Limit to top 3 tags
                    'created_at': formatted_date
                }
                
                processed_jobs.append(processed_job)
            
            return render_template('jobs.html', jobs=processed_jobs, form=form)
        
        except Exception as e:
            print(f"Error in jobs route: {e}")
            flash(f"Error fetching jobs: {str(e)}", 'danger')
            return render_template('jobs.html', jobs=[], form=form)

    @app.route('/job/<slug>')
    def job_detail(slug):

            try:
                # First, check if job exists in the database
                job = Job.query.filter_by(slug=slug).first()
                
                # If not in database, fetch from API
                if not job:
                    # Fetch all jobs from API 
                    jobs_data = fetch_jobs()
                    
                    # Find the job with matching slug
                    job_data = next((j for j in jobs_data if j.get('slug') == slug), None)

                    if not job_data:
                        flash('Job not found.', 'danger')
                        return redirect(url_for('jobs'))
                    
                    created_at = job_data.get('created_at')
                    # Create a new Job record in the database
                    job = Job(
                        slug=job_data.get('slug'),
                        title=job_data.get('title', 'Untitled Position'),
                        company=job_data.get('company_name', 'Unknown Company'),
                        location=job_data.get('location', 'Remote'),
                        description=job_data.get('description', ''),
                        posted_at=datetime.fromisoformat(job_data.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')) if created_at and isinstance(created_at,str) else datetime.now()
                    )
                    
                    # Add additional attributes from API data
                    job_data['remote'] = job_data.get('remote', False)
                    job_data['apply_url'] = job_data.get('url', '')
                    job_data['tags'] = extract_job_tags(job_data.get('title', ''), job_data.get('description', ''))
                    
                    # Format the date
                    created_at = job_data.get('created_at')
                    if created_at:
                        try: 
                            if created_at and isinstance(created_at,str):
                               date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            else:
                               date_obj = datetime.now()
                            days_ago = (datetime.now(date_obj.tzinfo) - date_obj).days
                            
                            if days_ago == 0:
                                job_data['created_at'] = "Today"
                            elif days_ago == 1:
                                job_data['created_at'] = "Yesterday"
                            else:
                                job_data['created_at'] = f"{days_ago} days ago"
                        except:
                            job_data['created_at'] = "Recently"
                    else:
                        job_data['created_at'] = "Recently"
                    
                    # Save to database
                    db.session.add(job)
                    db.session.commit()
                else:
                    # Convert the SQLAlchemy model to a dictionary for template rendering
                    job = {
                        'id': job.id,
                        'slug': job.slug,
                        'title': job.title,
                        'company_name': job.company,
                        'location': job.location,
                        'description': job.description or '',
                        'remote': True if 'remote' in job.location.lower() else False,
                        'created_at': "Today" if (datetime.now() - job.posted_at).days == 0 else 
                                    "Yesterday" if (datetime.now() - job.posted_at).days == 1 else
                                    f"{(datetime.now() - job.posted_at).days} days ago",
                        'tags': extract_job_tags(job.title, job.description),
                        'apply_url': f"https://www.arbeitnow.com/view/{job.slug}" if job.slug else None
                    }

                job_skills = extract_skills_from_text(job.get('description'))
                # For authenticated users, calculate skills match
                skills_match = []
                match_percentage = 0
                
                if current_user.is_authenticated:
                    # Get user skills
                    user_resume = Resume.query.filter_by(user_id=current_user.id).first()
                    
                    user_skills = []
                    
                    if user_resume and user_resume.resume_data and 'skills' in user_resume.resume_data:
                       user_skills_data = user_resume.resume_data['skills']

                       # Handle different formats of skills data
                       if isinstance(user_skills_data, str):
                         user_skills = [skill.strip() for skill in user_skills_data.split(',')]
                       elif isinstance(user_skills_data, list):
                         user_skills = user_skills_data

                    match_percentage, skills_match = calculate_skill_match(user_skills, job_skills)
                  
                # Add job skills to the session for use in resume creation
                session['job_skills'] = list(job_skills.keys())
                # Find similar jobs using skills overlap
                similar_jobs = find_similar_jobs(slug, job_skills, limit=3)
                
                
                return render_template(
                    'job_detail.html',
                    job=job,
                    skills_match=skills_match,
                    match_percentage=match_percentage,
                    similar_jobs=similar_jobs
                )
            
            except Exception as e:
                print(f"Error in job detail route: {e}")
                flash(f"Error loading job details: {str(e)}", 'danger')
                return redirect(url_for('jobs'))
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # Redirect if user is already logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = RegistrationForm()
        
        if form.validate_on_submit():
            try:
                # Check if email already exists using SQLAlchemy
                existing_user = User.query.filter_by(email=form.email.data).first()
                
                if existing_user:
                    flash('Email already registered. Please log in.', 'danger')
                    return redirect(url_for('login'))
                
                hashed_password = generate_password_hash(form.password.data)
                # Create new user with SQLAlchemy model
                new_user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password_hash=hashed_password
                )
                
                # Add and commit to database
                db.session.add(new_user)
                db.session.commit()
                
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                db.session.rollback()  # Roll back the session on error
                print(f"Registration error: {e}")
                flash('An error occurred during registration. Please try again.', 'danger')
        
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Redirect if user is already logged in
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            try:
                # Get user by email using SQLAlchemy
                user = User.query.filter_by(email=form.email.data).first()
                
                if user:
                    # Verify password
                    if check_password_hash(user.password_hash, form.password.data):
                        # Log in user
                        login_user(user)
                        
                        # Get next page or default to dashboard
                        next_page = request.args.get('next')
                        flash('Login successful!', 'success')
                        return redirect(next_page or url_for('dashboard'))
                    else:
                        flash('Invalid password. Please try again.', 'danger')
                else:
                    flash('Email not found. Please check your email or register.', 'danger')
            
            except Exception as e:
                print(f"Login error: {e}")
                flash('An error occurred during login. Please try again.', 'danger')
        
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))



    @app.route('/resume/start/<int:job_id>')
    @login_required
    def start_resume(job_id):
        job = Job.query.get_or_404(job_id)
        resume = Resume(user_id=current_user.id, job_id=job.id, resume_data={})
        db.session.add(resume)
        db.session.commit()
        skills = analyze_job_description(job.description)
        session['skills'] = skills
        flash('Resume creation started! Let\'s add your contact information.', 'success')
        return redirect(url_for('resume_contact', resume_id=resume.id))

    @app.route('/resume/<int:resume_id>/contact', methods=['GET', 'POST'])
    @login_required
    def resume_contact(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = ContactForm()

        if form.validate_on_submit():
            if resume.resume_data is None:
               resume.resume_data = {}
            resume.resume_data['contact'] = {
                'name': form.name.data,
                'email': form.email.data,
                'phone': form.phone.data,
                'location': request.form.get('location', ''),
                'linkedin': request.form.get('linkedin', ''),
                'website': request.form.get('website', '')
            }
            try:
              attributes.flag_modified(resume, 'resume_data')
              db.session.commit()
              flash('Contact information saved successfully!', 'success')
              return redirect(url_for('resume_skills', resume_id=resume.id))
            except Exception as e:
              db.session.rollback()
              print(f"Error saving contact info: {str(e)}")
              flash(f"Error saving contact information: {str(e)}", 'danger')

        if resume.resume_data and 'contact' in resume.resume_data:
            form.name.data = resume.resume_data['contact'].get('name', '')
            form.email.data = resume.resume_data['contact'].get('email', '')
            form.phone.data = resume.resume_data['contact'].get('phone', '')
        return render_template('resume_contact.html', form=form, resume=resume)

    @app.route('/resume/<int:resume_id>/summary', methods=['GET', 'POST'])
    @login_required
    def resume_summary(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        if resume.resume_data is None:
            resume.resume_data = {}
        
        form = SummaryForm()
        # Handle form submission
        if form.validate_on_submit():
            # Store summary as structured data
            resume.resume_data['summary'] = {
                'content': form.summary.data,
                'last_updated': datetime.now().isoformat()
            }
            attributes.flag_modified(resume, 'resume_data')
            # Save changes
            try:
                # Save changes
                db.session.commit()
                flash('Summary saved successfully!', 'success')
                return redirect(url_for('resume_preview', resume_id=resume.id))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving summary: {str(e)}")
                flash(f"Error saving summary: {str(e)}", 'danger')
        
        # Pre-populate form for GET requests
        if 'summary' in resume.resume_data:
            # Handle both formats (string or dictionary)
            if isinstance(resume.resume_data['summary'], dict):
                form.summary.data = resume.resume_data['summary'].get('content', '')
            else:
                form.summary.data = resume.resume_data['summary']
        
        # Render the form template
        return render_template(
            'resume_summary.html', 
            form=form, 
            resume=resume, 
            skills=session.get('skills', [])
        )

    @app.route('/resume/<int:resume_id>/experience', methods=['GET', 'POST'])
    @login_required
    def resume_experience(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        form = ExperienceForm()
        if request.method == 'POST' and request.form.get('experience_data'):
            if form.csrf_token.validate(form):
                try:
                    if resume.resume_data is None:
                       resume.resume_data = {}
                    # Get and debug the experience data
                    experience_data = request.form.get('experience_data')
                    print(f"Received experience_data: {experience_data}")
                    
                    if experience_data and experience_data.strip():
                        # Store as parsed JSON
                        experiences_json = json.loads(experience_data)
                        resume.resume_data['experience'] = experiences_json
                        print(f"Saved experiences: {experiences_json}")
                        attributes.flag_modified(resume, 'resume_data')
                        # Commit and redirect
                        db.session.commit()
                        flash('Experience information saved successfully!', 'success')
                        return redirect(url_for('resume_education', resume_id=resume.id))
                    else:
                        print("No experience data received")
                        flash("Please add at least one work experience", "warning")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error processing experience data: {str(e)}")
                    flash(f"Error saving experiences: {str(e)}", "danger")
            else:
               flash('CSRF validation failed.', 'danger')
    
        # Extract experiences from resume data for rendering
        experiences = []
        if resume.resume_data and 'experience' in resume.resume_data:
            experiences_data = resume.resume_data['experience']
            if isinstance(experiences_data, list):
                experiences = experiences_data
            else:
                # Handle single experience object
                experiences = [experiences_data]
        
        print(f"Rendering with experiences: {experiences}")
    
        return render_template('resume_experience.html', form=form, resume=resume, 
                          experiences=experiences, skills=session.get('skills', []))

    @app.route('/resume/<int:resume_id>/education', methods=['GET', 'POST'])
    @login_required
    def resume_education(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = EducationForm()

        if request.method == 'POST' and request.form.get('education_data'):
            if resume.resume_data is None:
              resume.resume_data = {}
            try:
                educations_json = json.loads(request.form.get('education_data'))
                resume.resume_data['education'] = educations_json
                attributes.flag_modified(resume, 'resume_data')
                db.session.commit()
                flash('Education information saved successfully!', 'success')
                return redirect(url_for('resume_summary', resume_id=resume.id))
            except Exception as e:
                db.session.rollback()
                print(f"Error processing education data: {str(e)}")
                flash(f"Error saving education: {str(e)}", 'danger')
        if resume.resume_data and 'education' in resume.resume_data:
            edu = resume.resume_data['education']
            form.degree.data = edu.get('degree', '')
            form.school.data = edu.get('school', '')
            form.year.data = edu.get('year', '')
        return render_template('resume_education.html', form=form, resume=resume)

    @app.route('/resume/<int:resume_id>/skills', methods=['GET', 'POST'])
    @login_required
    def resume_skills(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        form = SkillsForm()
        if form.validate_on_submit() and form.skills.data :
            if resume.resume_data is None:
              resume.resume_data = {}
            resume.resume_data['skills'] = form.skills.data
            attributes.flag_modified(resume, 'resume_data')
            try:
               db.session.commit()
               flash('Skills saved successfully!', 'success')
               return redirect(url_for('resume_experience', resume_id=resume.id))
            except Exception as e:
               db.session.rollback()
               print(f"Error saving skills: {str(e)}")
               flash(f"Error saving skills: {str(e)}", 'danger')
            # Get suggested skills
        suggested_skills = []
        if resume.job:
            # Extract skills from job description
            job_skills = extract_skills_from_text(resume.job.description)
            # Sort by importance and take top skills
            suggested_skills = sorted(job_skills.items(), key=lambda x: x[1], reverse=True)
            suggested_skills = [skill for skill, _ in suggested_skills[:15]]
        # Pre-populate form
        if resume.resume_data and 'skills' in resume.resume_data:
            form.skills.data = resume.resume_data['skills']
        return render_template('resume_skills.html', form=form, resume=resume, suggested_skills=suggested_skills)

    @app.route('/resume/<int:resume_id>/preview')
    @login_required
    def resume_preview(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        from resume_templates import RESUME_TEMPLATES
        return render_template('resume_template.html', resume=resume, job=resume.job,templates=RESUME_TEMPLATES)

    @app.route('/resume/<int:resume_id>/download')
    @login_required
    def resume_download(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        html = render_template('resume_template.html', **resume.resume_data, job=resume.job)
        pdf = generate_pdf(html)
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'resume_for_{resume.job.slug}.pdf'
        )

    @app.route('/resume/<int:resume_id>/delete', methods=['POST'])
    @login_required
    def delete_resume(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)  # Forbidden if not the owner

        try:
            db.session.delete(resume)
            db.session.commit()
            return jsonify({"success": True,"message": "Resume deleted successfully"})
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting resume: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get user's resumes
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        
        # Process resumes for display
        for resume in resumes:
            # Handle general resumes (without a job)
                   # Set display values explicitly
            if resume.job:
                resume.display_title = f"Resume for {resume.job.title}"
                resume.display_company = resume.job.company
                resume.display_match = 85  # Or calculate actual match
            else:
                resume.display_title = resume.title or "General Resume"
                resume.display_company = "Multiple Companies"
                resume.display_match = 30  # General resumes show 100%
                
                # Add match score for general resumes (could be based on completeness)
            resume.match_score = calculate_resume_completeness(resume.resume_data)
            
        # Get job matches count
        job_matches = 3  # This would be calculated based on  matching algorithm
        
        # Get sample job matches list ( TODO:this would come from  database)
        job_matches_list = [
            {
                'slug': 'software-engineer-xyz-company',
                'title': 'Software Engineer',
                'company_name': 'XYZ Tech',
                'location': 'San Francisco, CA',
                'remote': True,
                'match': 92
            },
            {
                'slug': 'frontend-developer-abc-inc',
                'title': 'Frontend Developer',
                'company_name': 'ABC Inc',
                'location': 'New York, NY',
                'remote': False,
                'match': 87
            },
            {
                'slug': 'fullstack-engineer-startup',
                'title': 'Fullstack Engineer',
                'company_name': 'Startup Co',
                'location': 'Austin, TX',
                'remote': True,
                'match': 84
            }
        ]
        
        # Placeholder for applications count
        applications = 0
        
        return render_template(
            'dashboard.html', 
            resumes=resumes,
            job_matches=job_matches,
            job_matches_list=job_matches_list,
            applications=applications
        )

    @app.route('/pricing')
    def pricing():
        return render_template('pricing.html')

    @app.route('/resume/<int:resume_id>/view')
    @login_required
    def view_resume(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to view this resume.', 'danger')
            return redirect(url_for('dashboard'))
        
        # return render_template('view_resume.html', resume=resume)
        # Temp
        return render_template('resume_template.html', resume=resume)
    

    @app.route('/resume/<int:resume_id>/pdf')
    @login_required
    def generate_pdf(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        
        # Check if the resume belongs to the current user
        if resume.user_id != current_user.id:
            flash('You do not have permission to access this resume.', 'danger')
            return redirect(url_for('dashboard'))
         # Prepare the resume name for the PDF file
        if resume.job:
           filename = f"resume_{current_user.username}_{resume.job.title}.pdf"
        else:
           filename = f"resume_{current_user.username}.pdf"
        filename = filename.replace(' ', '_')

        try:
                from resume_templates import RESUME_TEMPLATES
                # Get template info
                template_info = RESUME_TEMPLATES.get(resume.template, RESUME_TEMPLATES['standard'])
                template_class = template_info['css_class']
                # Create a file-like buffer to receive PDF data
                buffer = BytesIO()
                
                # Create the PDF document using ReportLab
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=letter,
                    rightMargin=0.75*inch,
                    leftMargin=0.75*inch,
                    topMargin=0.75*inch,
                    bottomMargin=0.75*inch
                )
                
                # Define styles
                styles = getSampleStyleSheet()
                 # Create template-specific styles
                if template_class == 'template-modern':
                    # Modern template styles
                    resume_title_style = ParagraphStyle(
                        name='ResumeTitle',
                        parent=styles['Heading1'],
                        alignment=0,  # Left alignment
                        fontSize=20,
                        spaceAfter=12,
                        textColor=colors.blue
                    )
                    
                    section_heading_style = ParagraphStyle(
                        name='ResumeSectionHeading',
                        parent=styles['Heading2'],
                        fontSize=14,
                        textColor=colors.blue,
                        spaceAfter=8,
                        bulletIndent=10
                    )
                    
                    contact_info_style = ParagraphStyle(
                        name='ResumeContactInfo',
                        parent=styles['Normal'],
                        alignment=0,  # Left alignment
                        fontSize=10,
                        spaceAfter=12
                    )
                elif template_class == 'template-minimal':
                        # Minimal template styles
                        resume_title_style = ParagraphStyle(
                            name='ResumeTitle',
                            parent=styles['Heading1'],
                            alignment=0,  # Left alignment
                            fontSize=22,
                            fontName='Helvetica',
                            spaceAfter=8
                        )
                        
                        section_heading_style = ParagraphStyle(
                            name='ResumeSectionHeading',
                            parent=styles['Heading2'],
                            fontSize=12,
                            fontName='Helvetica-Bold',
                            textTransform='uppercase',
                            spaceAfter=6,
                            textColor=colors.black
                        )
                        
                        contact_info_style = ParagraphStyle(
                            name='ResumeContactInfo',
                            parent=styles['Normal'],
                            alignment=0,  # Left alignment
                            fontSize=9,
                            fontName='Helvetica',
                            textColor=colors.gray
                        )
                elif template_class == 'template-executive':
                        # Executive template styles
                        resume_title_style = ParagraphStyle(
                            name='ResumeTitle',
                            parent=styles['Heading1'],
                            alignment=1,  # Center alignment
                            fontSize=20,
                            spaceAfter=12,
                            fontName='Times-Bold'
                        )
                        
                        section_heading_style = ParagraphStyle(
                            name='ResumeSectionHeading',
                            parent=styles['Heading2'],
                            fontSize=14,
                            fontName='Times-Bold',
                            textTransform='uppercase',
                            borderWidth=1,
                            borderColor=colors.black,
                            borderPadding=(0, 0, 1, 0),  # bottom border only
                            spaceAfter=8
                        )
                        
                        contact_info_style = ParagraphStyle(
                            name='ResumeContactInfo',
                            parent=styles['Normal'],
                            alignment=1,  # Center alignment
                            fontSize=10,
                            fontName='Times-Roman',
                            spaceAfter=14
                        )
            
                else:
                        # Standard template (default)
                        resume_title_style = ParagraphStyle(
                            name='ResumeTitle',
                            parent=styles['Heading1'],
                            alignment=1,  # Center alignment
                            fontSize=18,
                            spaceAfter=12
                        )
                        
                        section_heading_style = ParagraphStyle(
                            name='ResumeSectionHeading',
                            parent=styles['Heading2'],
                            fontSize=14,
                            textColor=colors.blue,
                            spaceAfter=6
                        )
                        
                        contact_info_style = ParagraphStyle(
                            name='ResumeContactInfo',
                            parent=styles['Normal'],
                            alignment=1,  # Center alignment
                            fontSize=10,
                            spaceAfter=12
                        )
           
                 # Create normal text style based on template
                normal_text_style = ParagraphStyle(
                    name='NormalText',
                    parent=styles['Normal'],
                    fontName='Helvetica' if template_class == 'template-minimal' else 'Times-Roman' if template_class == 'template-executive' else 'Helvetica',
                    fontSize=10
                )
                # Build the document content
                elements = []
                
                # Add contact information
                contact = resume.resume_data.get('contact', {})
                elements.append(Paragraph(contact.get('name', 'Your Name'), resume_title_style))
                
                contact_text = []
                if contact.get('email'):
                    contact_text.append(contact.get('email'))
                if contact.get('phone'):
                    contact_text.append(contact.get('phone'))
                if contact.get('location'):
                    contact_text.append(contact.get('location'))
                
                elements.append(Paragraph(' | '.join(contact_text), contact_info_style))
                
                if contact.get('linkedin') or contact.get('website'):
                    website_text = []
                    if contact.get('linkedin'):
                        website_text.append(contact.get('linkedin'))
                    if contact.get('website'):
                        website_text.append(contact.get('website'))
                    elements.append(Paragraph(' | '.join(website_text), contact_info_style))
                
                elements.append(Spacer(1, 0.2*inch))
                
                # Add summary if available
                if resume.resume_data.get('summary'):
                    elements.append(Paragraph('Professional Summary', section_heading_style))
                    
                    summary_text = resume.resume_data.get('summary')
                    if not isinstance(summary_text, str):
                        summary_text = summary_text.get('content', '')
                    
                    elements.append(Paragraph(summary_text, styles['Normal']))
                    elements.append(Spacer(1, 0.2*inch))
                
                # Add experience if available
                if resume.resume_data.get('experience'):
                    elements.append(Paragraph('Work Experience', section_heading_style))
                    
                    for exp in resume.resume_data.get('experience'):
                        title_company = f"<b>{exp.get('title')}</b> - {exp.get('company')}"
                        elements.append(Paragraph(title_company, styles['Normal']))
                        
                        date_range = f"{exp.get('startDate')} - {'Present' if exp.get('current') else exp.get('endDate')}"
                        elements.append(Paragraph(f"<i>{date_range}</i>", styles['Normal']))
                        
                        if exp.get('description'):
                            for line in exp.get('description').split('\n'):
                                if line.strip():
                                    elements.append(Paragraph(f"• {line.strip()}", styles['Normal']))
                        
                        elements.append(Spacer(1, 0.1*inch))
                    
                    elements.append(Spacer(1, 0.1*inch))
                
                # Add education if available
                if resume.resume_data.get('education'):
                    elements.append(Paragraph('Education', section_heading_style))
                    
                    education_data = resume.resume_data.get('education')
                    if isinstance(education_data, dict):
                        # Single education entry
                        degree = education_data.get('degree', '')
                        school = education_data.get('school', '')
                        year = education_data.get('year', '')
                        
                        elements.append(Paragraph(f"<b>{degree}</b>", styles['Normal']))
                        elements.append(Paragraph(f"{school}", styles['Normal']))
                        elements.append(Paragraph(f"<i>{year}</i>", styles['Normal']))
                    elif isinstance(education_data, list):
                        # Multiple education entries
                        for edu in education_data:
                            degree = edu.get('degree', '')
                            school = edu.get('school', '')
                            start_year = edu.get('startYear', '')
                            end_year = 'Present' if edu.get('current') else edu.get('endYear', '')
                            date_range = f"{start_year} - {end_year}"
                            
                            elements.append(Paragraph(f"<b>{degree}</b>", styles['Normal']))
                            elements.append(Paragraph(f"{school}", styles['Normal']))
                            elements.append(Paragraph(f"<i>{date_range}</i>", styles['Normal']))
                            
                            if edu.get('description'):
                                elements.append(Paragraph(edu.get('description'), styles['Normal']))
                            
                            elements.append(Spacer(1, 0.1*inch))
                    
                    elements.append(Spacer(1, 0.1*inch))
                
                # Add skills if available
                if resume.resume_data.get('skills'):
                    elements.append(Paragraph('Skills', section_heading_style))
                    
                    skills_text = resume.resume_data.get('skills')
                    if isinstance(skills_text, str):
                        skills_list = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
                    else:
                        skills_list = skills_text
                    
                    # Create a table for skills with 3 columns
                    if skills_list:
                        # Organize skills into rows of 3
                        skill_rows = []
                        row = []
                        for skill in skills_list:
                            row.append(skill)
                            if len(row) == 3:
                                skill_rows.append(row)
                                row = []
                        
                        if row:  # Add any remaining skills
                            while len(row) < 3:
                                row.append('')
                            skill_rows.append(row)
                        
                        # Create the skills table
                        skills_table = Table(skill_rows, colWidths=[2*inch, 2*inch, 2*inch])
                        skills_table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ]))
                        
                        elements.append(skills_table)
                
                # Build the PDF document
                doc.build(elements)
                
                # Get the PDF value from the buffer
                pdf_value = buffer.getvalue()
                buffer.close()
                
                # Create response with PDF
                response = make_response(pdf_value)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                return response
                
        except Exception as e:
                print(f"Error generating PDF: {str(e)}")
                flash(f"Error generating PDF: {str(e)}", 'danger')
                return redirect(url_for('resume_preview', resume_id=resume.id))


   
    @app.route('/resume/create/general')
    @login_required
    def create_general_resume():
        """
        Create a general resume not tied to any specific job
        """
        try:
            # Create a new resume without a job_id
            resume = Resume(
                user_id=current_user.id,
                resume_data={},
                title="General Resume"  # Default title for general resumes
            )
            
            # Add to database
            db.session.add(resume)
            db.session.commit()
            
            # Set default skills list (empty for general resume)
            session['skills'] = []
            
            # Redirect to the first step of resume creation
            flash('General resume creation started! Let\'s add your contact information.', 'success')
            return redirect(url_for('resume_contact', resume_id=resume.id))
        
        except Exception as e:
            print(f"Error creating general resume: {e}")
            flash(f"Error creating resume: {str(e)}", 'danger')
            return redirect(url_for('dashboard'))

    @app.route('/resume/<int:resume_id>/template')
    @login_required
    def select_resume_template(resume_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
        from resume_templates import RESUME_TEMPLATES
        
        return render_template('resume_template_select.html', 
                            resume=resume, 
                            templates=RESUME_TEMPLATES)


    @app.route('/resume/<int:resume_id>/template/<template_id>')
    @login_required
    def set_resume_template(resume_id, template_id):
        resume = Resume.query.get_or_404(resume_id)
        if resume.user_id != current_user.id:
            abort(403)
        
       
        from resume_templates import RESUME_TEMPLATES
        
        # Check if the template_id is valid
        if template_id in RESUME_TEMPLATES:
            # Update the resume with the selected template
            resume.template = template_id
            
            try:
                db.session.commit()
                flash('Resume template updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating template: {str(e)}', 'danger')
        else:
            flash('Invalid template selection.', 'danger')
        
        return redirect(url_for('select_resume_template', resume_id=resume.id))


    @app.route('/applications')
    @login_required
    def applications():
        # Get all applications for current user
        user_applications = Application.query.filter_by(user_id=current_user.id).order_by(Application.applied_date.desc()).all()
        
        # Group by status
        applications_by_status = {
            'applied': [],
            'interviewing': [],
            'offered': [],
            'rejected': [],
            'accepted': []
        }
        
        for app in user_applications:
            applications_by_status[app.status].append(app)
        
        return render_template('applications.html', applications=user_applications, grouped=applications_by_status)

    @app.route('/jobs/<slug>/apply', methods=['GET', 'POST'])
    @login_required
    def apply_to_job(slug):
        job = Job.query.filter_by(slug=slug).first_or_404()
        
        # Check if already applied
        existing_application = Application.query.filter_by(
            user_id=current_user.id,
            job_id=job.id
        ).first()
        
        if existing_application:
            flash('You have already applied to this job.', 'info')
            return redirect(url_for('application_details', application_id=existing_application.id))
        
        # Get user's resumes
        resumes = Resume.query.filter_by(user_id=current_user.id).all()
        
        if request.method == 'POST':
            resume_id = request.form.get('resume_id')
            
            # Create application
            application = Application(
                user_id=current_user.id,
                job_id=job.id,
                resume_id=resume_id if resume_id else None,
                status='applied'
            )
            try:
              db.session.add(application)
              db.session.commit()
              flash('Application submitted successfully!', 'success')
              return redirect(url_for('application_details', application_id=application.id))
            except Exception as e:
              db.session.rollback()
              print(f'error creating application:{e}')
              flash(f'Error creating application: {str(e)}', 'danger')
              
            
            
        
        return render_template('apply_job.html', job=job, resumes=resumes)


    @app.route('/applications/<int:application_id>', methods=['GET', 'POST'])
    @login_required
    def application_details(application_id):
        application = Application.query.get_or_404(application_id)
        
        # Check if current user owns this application
        if application.user_id != current_user.id:
            abort(403)
        
        form = ApplicationForm(obj=application)
        
        if form.validate_on_submit():
            # Update application
            application.status = form.status.data
            application.notes = form.notes.data
            
            db.session.commit()
            flash('Application updated successfully!', 'success')
            return redirect(url_for('applications'))
        
        # Get application timeline TODO:
        timeline = []
        
        return render_template('application_details.html', application=application, form=form, timeline=timeline)