from flask import Flask, request, jsonify
from agents import ResumeAnalyzer
from models import UserProfile
from models import JobSearchParams

app = Flask(__name__)
resume_analyzer = ResumeAnalyzer()

@app.route('/analyze', methods=['POST'])
async def analyze_resume():
    try:
        data = request.json
        
        # Parse input data
        user_profile = UserProfile(**data['user_profile'])
        job_params = JobSearchParams(**data['job_params'])
        application_question = data.get('application_question')

        # Run analysis
        result = await resume_analyzer.analyze_resume_and_jd(
            user_profile=user_profile,
            job_params=job_params,
            application_question=application_question
        )

        return jsonify(result.dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
