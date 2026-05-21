from multiprocessing import Process
from flask import Blueprint, jsonify, request
from app.middlewares.require_internal import require_internal
from ..services.quiz_mail_service import QuizMailService
from ..services.quiz_pdf_service import PDFService
from ..services.quiz_service import QuizService
from ..services.quiz_attempts_service import AttemptsService

quiz_mail_bp = Blueprint("quiz_mail", __name__, url_prefix="/quiz-mail")

@quiz_mail_bp.route("/reports", methods=["POST"])
@require_internal
def generate_report():

    data = request.get_json()
    current_user_email = data.get("admin_email")
    quiz_ids = data.get("quiz_ids")
    users = data.get("users")

    quizzes = QuizService.get_quiz_titles(quiz_ids)
    attempts = AttemptsService.get_attempts_for_quizzes(quiz_ids)

    if not users or not isinstance(users, list):
        return jsonify({"error": "users must be a list"}), 400

    if not quizzes or not isinstance(quizzes, list):
        return jsonify({"error": "quiz_ids must be a list"}), 400

    pdf_bytes = PDFService.generate_report(quizzes, users, attempts)

    Process(target=QuizMailService.send_email_pdf, args=(current_user_email, pdf_bytes,[q["title"] for q in quizzes])).start()


    return jsonify({
        "message": "Reports generation started, check your mailbox"
    }), 202
