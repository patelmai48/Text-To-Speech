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
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
    """Retrieve user conversion history with optional search query."""
    search = request.args.get('search', '').strip()
    query = History.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(History.text.ilike(f'%{search}%'))

    history_records = query.order_by(History.created_at.desc()).all()
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
    items = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Text', 'Language', 'Voice', 'Speed', 'Character Count', 'Created At'])

    for item in items:
        writer.writerow([
            item.id,
            item.text.replace('\n', ' '),
            item.language,
            item.voice,
            item.speed,
            item.character_count,
            item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
        ])

    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'tts_history_{current_user.username}.csv'
    )

@tts_bp.route('/history/export/pdf', methods=['GET'])
@token_required
@verification_required
def export_pdf(current_user):
    """Export history as downloadable PDF report."""
    items = History.query.filter_by(user_id=current_user.id).order_by(History.created_at.desc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#4F46E5'))
    story.append(Paragraph(f"AI Text-to-Speech History Report", title_style))
    story.append(Paragraph(f"User: <b>{current_user.username}</b> ({current_user.email})", styles['Normal']))
    story.append(Spacer(1, 15))

    data = [['ID', 'Text', 'Voice', 'Chars', 'Created At']]
    for item in items:
        text_snippet = (item.text[:40] + '...') if len(item.text) > 40 else item.text
        data.append([
            str(item.id),
            Paragraph(text_snippet, styles['Normal']), # type: ignore
            item.voice,
            str(item.character_count),
            item.created_at.strftime('%Y-%m-%d %H:%M') if item.created_at else ''
        ])

    table = Table(data, colWidths=[30, 260, 90, 50, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))

    story.append(table)
    doc.build(story)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'tts_history_{current_user.username}.pdf'
    )

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
