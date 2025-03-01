from flask import request, jsonify, render_template
from modules.models import db, PaymentInfo
import logging 


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def get_payment_info():
    """Получение всех платежных данных"""
    payments = PaymentInfo.query.order_by(PaymentInfo.created_at.desc()).all()
    return [payment.to_dict() for payment in payments]

def add_payment_info():
    """Добавление новых платежных данных"""
    try:
        account_number = request.form.get('account_number')
        bank_name = request.form.get('bank_name')
        recipient_name = request.form.get('recipient_name')

        if not all([account_number, bank_name, recipient_name]):
            logger.warning('Попытка добавления платежных данных с неполными полями')
            return jsonify({'error': 'Все поля должны быть заполнены'}), 400

        payment = PaymentInfo(
            account_number=account_number,
            bank_name=bank_name,
            recipient_name=recipient_name,
            active=True
        )
        db.session.add(payment)
        db.session.commit()
        logger.info(f'Добавлены новые платежные данные: {payment.id}')
        return jsonify({'success': True, 'payment': payment.to_dict()}), 200
    except Exception as e:
        logger.error(f'Ошибка при добавлении платежных данных: {str(e)}')
        return jsonify({'error': str(e)}), 500

def delete_payment_info(payment_id):
    """Удаление платежных данных"""
    try:
        payment = PaymentInfo.query.get_or_404(payment_id)
        db.session.delete(payment)
        db.session.commit()
        logger.info(f'Удалены платежные данные: {payment_id}')
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'Ошибка при удалении платежных данных {payment_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500

def payment_page():
    """Страница управления платежными данными"""
    payments = get_payment_info()
    return render_template('payment.html', payments=payments)

def toggle_payment_status(payment_id):
    """Переключение статуса активности платежных данных"""
    try:
        payment = PaymentInfo.query.get_or_404(payment_id)
        payment.active = not payment.active
        db.session.commit()
        logger.info(f'Изменен статус платежных данных {payment_id}: active={payment.active}')
        return jsonify({'success': True, 'active': payment.active}), 200
    except Exception as e:
        logger.error(f'Ошибка при изменении статуса платежных данных {payment_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500

def get_payment_api():
    """API endpoint для получения платежных данных"""
    try:
        active_payments = PaymentInfo.query.filter_by(active=True).all()
        
        if active_payments:
            logger.info('Запрошены активные платежные данные')
            return jsonify({
                'success': True,
                'payments': [{
                    'id': payment.id,
                    'account_number': payment.account_number,
                    'bank_name': payment.bank_name,
                    'recipient_name': payment.recipient_name,
                    'active': payment.active
                } for payment in active_payments]
            }), 200
        else:
            logger.warning('Запрос активных платежных данных: данные отсутствуют')
            return jsonify({
                'success': False,
                'error': 'Нет активных платежных данных'
            }), 404
            
    except Exception as e:
        logger.error(f'Ошибка при получении активных платежных данных: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def get_all_payments_api():
    """API endpoint для получения всех платежных данных"""
    try:
        payments = PaymentInfo.query.order_by(PaymentInfo.created_at.desc()).all()
        logger.info('Запрошены все платежные данные')
        return jsonify({
            'success': True,
            'payments': [{
                'id': payment.id,
                'account_number': payment.account_number,
                'bank_name': payment.bank_name,
                'recipient_name': payment.recipient_name,
                'active': payment.active
            } for payment in payments]
        }), 200
    except Exception as e:
        logger.error(f'Ошибка при получении всех платежных данных: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def update_payment_info(payment_id):
    """Обновление платежных данных"""
    try:
        payment = PaymentInfo.query.get_or_404(payment_id)
        
        account_number = request.form.get('account_number')
        bank_name = request.form.get('bank_name')
        recipient_name = request.form.get('recipient_name')

        if not all([account_number, bank_name, recipient_name]):
            logger.warning(f'Попытка обновления платежных данных {payment_id} с неполными полями')
            return jsonify({'error': 'Все поля должны быть заполнены'}), 400

        payment.account_number = account_number
        payment.bank_name = bank_name
        payment.recipient_name = recipient_name
        
        db.session.commit()
        logger.info(f'Обновлены платежные данные: {payment_id}')
        return jsonify({'success': True, 'payment': payment.to_dict()}), 200
    except Exception as e:
        logger.error(f'Ошибка при обновлении платежных данных {payment_id}: {str(e)}')
        return jsonify({'error': str(e)}), 500 