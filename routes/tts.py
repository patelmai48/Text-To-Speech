import os
import sys

# Add parent directory to sys.path to ensure IDE linters and Flask resolve top-level modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import csv
import io
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, History, Favorite, Summary
from routes.auth import token_required, verification_required
from services.speech import generate_speech, summarize_text, SUPPORTED_LANGUAGES, get_voice_meta
from services.reporting import CSVReportGenerator, PDFReportGenerator

tts_bp = Blueprint('tts', __name__)

@tts_bp.route('/voices', methods=['GET'])
def get_voices():
    """Retrieve list of available TTS voices and languages."""
    return jsonify({
        'success': True,
        'voices': SUPPORTED_LANGUAGES
    }), 200

@tts_bp.route('/languages', methods=['GET'])
def get_languages():
    """Retrieve unique list of supported languages."""
    unique_langs = {}
    for item in SUPPORTED_LANGUAGES:
        if item['code'] not in unique_langs:
            unique_langs[item['code']] = {
                'code': item['code'],
                'name': item['name'].split(' (')[0],
                'flag': item['flag']
            }
    return jsonify({
        'success': True,
        'languages': list(unique_langs.values())
    }), 200

@tts_bp.route('/tts', methods=['POST'])
@token_required
@verification_required
def create_tts(current_user):
    """Convert text to speech audio, save audio file and log to user history."""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    voice = data.get('voice', 'en-us').strip()
    language = data.get('language', 'en').strip()
    try:
        speed = float(data.get('speed', 1.0))
        pitch = float(data.get('pitch', 1.0))
        volume = float(data.get('volume', 1.0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid parameter format for speed, pitch, or volume.'}), 400

    if not (0.5 <= speed <= 2.0):
        return jsonify({'success': False, 'message': 'Speed must be between 0.5 and 2.0.'}), 400

    if not (0.5 <= pitch <= 2.0):
        return jsonify({'success': False, 'message': 'Pitch must be between 0.5 and 2.0.'}), 400

    if not (0.0 <= volume <= 1.0):
        return jsonify({'success': False, 'message': 'Volume must be between 0.0 and 1.0.'}), 400

    if not text:
        return jsonify({'success': False, 'message': 'Text input cannot be empty.'}), 400

    max_len = current_app.config.get('MAX_TEXT_LENGTH', 3000)
    if len(text) > max_len:
        return jsonify({'success': False, 'message': f'Text exceeds maximum limit of {max_len} characters.'}), 400

    output_dir = current_app.config.get('AUDIO_FOLDER', 'static/audio')

    try:
        filename, char_count = generate_speech(
            text=text,
            voice_id=voice,
            speed=speed,
            output_folder=output_dir
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Audio synthesis error: {str(e)}'}), 500

    # Save to history DB table
    history_item = History(
        user_id=current_user.id,
        text=text,
        language=language,
        voice=voice,
        speed=speed,
        pitch=pitch,
        volume=volume,
        audio_filename=filename,
        character_count=char_count
    )

    db.session.add(history_item)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Speech synthesized successfully!',
        'history': history_item.to_dict()
    }), 201

@tts_bp.route('/tts/summarize', methods=['POST'])
@token_required
@verification_required
def summarize(current_user):
    """Summarize text content and automatically save to user's Summaries collection."""
    data = request.get_json() or {}
    text = data.get('text', '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'Text content is required for summarization.'}), 400

    summary_text = summarize_text(text)
    
    # Save to summaries table
    summary_item = Summary(
        user_id=current_user.id,
        original_topic=text[:150],
        summary_content=summary_text
    )
    db.session.add(summary_item)
    db.session.commit()

    return jsonify({
        'success': True,
        'summary': summary_text,
        'saved_summary': summary_item.to_dict()
    }), 200

@tts_bp.route('/summaries', methods=['GET'])
@token_required
@verification_required
def get_summaries(current_user):
    """Retrieve saved summaries for current user."""
    summaries = Summary.query.filter_by(user_id=current_user.id).order_by(Summary.created_at.desc()).all()
    return jsonify({
        'success': True,
        'summaries': [s.to_dict() for s in summaries]
    }), 200

@tts_bp.route('/summaries/<int:summary_id>', methods=['DELETE'])
@token_required
@verification_required
def delete_summary(current_user, summary_id):
    """Delete a single summary item."""
    item = Summary.query.filter_by(id=summary_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': 'Summary item not found.'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Summary deleted successfully.'}), 200

@tts_bp.route('/history', methods=['GET'])
@token_required
@verification_required
def get_history(current_user):
    """Retrieve user conversion history with optional search query and pagination."""
    search = request.args.get('search', '').strip()
    page_param = request.args.get('page')
    per_page_param = request.args.get('per_page')

    query = History.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(History.text.ilike(f'%{search}%'))

    query = query.order_by(History.created_at.desc())

    if page_param is not None or per_page_param is not None:
        try:
            page = max(1, int(page_param or 1))
            per_page = min(100, max(1, int(per_page_param or 20)))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid page or per_page integer value.'}), 400

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            'success': True,
            'count': len(pagination.items),
            'total_count': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'history': [item.to_dict() for item in pagination.items]
        }), 200

    history_records = query.all()
    return jsonify({
        'success': True,
        'count': len(history_records),
        'history': [item.to_dict() for item in history_records]
    }), 200

@tts_bp.route('/history/<int:history_id>', methods=['DELETE'])
@token_required
@verification_required
def delete_history_item(current_user, history_id):
    """Delete a single history record and its associated audio file."""
    item = History.query.filter_by(id=history_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': 'History item not found or unauthorized.'}), 404

    # Remove audio file from disk
    if item.audio_filename:
        audio_path = os.path.join(current_app.config.get('AUDIO_FOLDER', 'static/audio'), item.audio_filename)
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass

    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'History item deleted successfully.'}), 200

@tts_bp.route('/history', methods=['DELETE'])
@token_required
@verification_required
def delete_all_history(current_user):
    """Clear all conversion history records for current user."""
    items = History.query.filter_by(user_id=current_user.id).all()
    audio_dir = current_app.config.get('AUDIO_FOLDER', 'static/audio')

    for item in items:
        if item.audio_filename:
            audio_path = os.path.join(audio_dir, item.audio_filename)
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
        db.session.delete(item)

    db.session.commit()
    return jsonify({'success': True, 'message': 'All history items cleared.'}), 200

@tts_bp.route('/history/export/csv', methods=['GET'])
@token_required
@verification_required
def export_csv(current_user):
    """Export history as downloadable CSV file."""
    try:
        items = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).all()
        csv_data = CSVReportGenerator.generate(items)

        mem = io.BytesIO()
        mem.write(csv_data.encode('utf-8'))
        mem.seek(0)

        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tts_history_{current_user.username}.csv'
        )
    except Exception as e:
        current_app.logger.error(f"CSV export failed for user {current_user.id}: {e}")
        return jsonify({'success': False, 'message': 'Failed to generate CSV export.'}), 500

@tts_bp.route('/history/export/pdf', methods=['GET'])
@token_required
@verification_required
def export_pdf(current_user):
    """Export history as downloadable PDF report."""
    try:
        items = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).all()
        pdf_buffer = PDFReportGenerator.generate(items, username=current_user.username)

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'tts_history_{current_user.username}.pdf'
        )
    except Exception as e:
        current_app.logger.error(f"PDF export failed for user {current_user.id}: {e}")
        return jsonify({'success': False, 'message': 'Failed to generate PDF export.'}), 500

@tts_bp.route('/favorites', methods=['GET'])
@token_required
@verification_required
def get_favorites(current_user):
    """Retrieve user favorite voices and languages."""
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'success': True,
        'favorites': [f.to_dict() for f in favs]
    }), 200

@tts_bp.route('/favorites', methods=['POST'])
@token_required
@verification_required
def add_favorite(current_user):
    """Add a voice or language to user favorites."""
    data = request.get_json() or {}
    item_type = data.get('item_type', 'voice').strip().lower()
    item_value = data.get('item_value', '').strip()

    if not item_value:
        return jsonify({'success': False, 'message': 'Item value is required.'}), 400

    existing = Favorite.query.filter_by(user_id=current_user.id, item_type=item_type, item_value=item_value).first()
    if existing:
        return jsonify({'success': True, 'message': 'Already in favorites.', 'favorite': existing.to_dict()}), 200

    fav = Favorite(user_id=current_user.id, item_type=item_type, item_value=item_value)
    db.session.add(fav)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Added to favorites!',
        'favorite': fav.to_dict()
    }), 201

@tts_bp.route('/favorites/<int:fav_id>', methods=['DELETE'])
@token_required
@verification_required
def remove_favorite(current_user, fav_id):
    """Remove item from favorites by ID."""
    fav = Favorite.query.filter_by(id=fav_id, user_id=current_user.id).first()
    if not fav:
        return jsonify({'success': False, 'message': 'Favorite item not found.'}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Removed from favorites.'}), 200
