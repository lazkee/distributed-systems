from multiprocessing import Process
from flask import Blueprint, jsonify, request
from app.middlewares.require_internal import require_internal
from app.logging_config import audit_log, get_request_ip
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

    try:
        QuizService.validate_approved_quiz_ids(quiz_ids)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    quizzes = QuizService.get_quiz_titles(quiz_ids)
    attempts = AttemptsService.get_attempts_for_quizzes(quiz_ids)

    if not users or not isinstance(users, list):
        return jsonify({"error": "users must be a list"}), 400

    if not quizzes or not isinstance(quizzes, list):
        return jsonify({"error": "quiz_ids must be a list"}), 400

    pdf_bytes = PDFService.generate_report(quizzes, users, attempts)

    Process(target=QuizMailService.send_email_pdf, args=(current_user_email, pdf_bytes, [q["title"] for q in quizzes])).start()

    audit_log.info(
        "report_generation_requested",
        quiz_count=len(quiz_ids),
        ip=get_request_ip(),
    )
    return jsonify({
        "message": "Reports generation started, check your mailbox"
    }), 202


@quiz_mail_bp.route("/reports/player-ids", methods=["POST"])
@require_internal
def get_report_player_ids():
    data = request.get_json()
    quiz_ids = data.get("quiz_ids")

    try:
        QuizService.validate_approved_quiz_ids(quiz_ids)
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400

    player_ids = AttemptsService.get_player_ids_for_quizzes(quiz_ids)
    audit_log.info("report_player_ids_requested", quiz_ids=quiz_ids, ip=get_request_ip())

    return jsonify({
        "success": True,
        "data": {"player_ids": player_ids}
    }), 200
