from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from db import db
import threading
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret'


TARIFFS = [
    {'name': 'Старт',    'price': 299, 'gb': '10 ГБ интернета',  'minutes': '100 минут звонков',  'sms': '50 SMS',  'extra': 'Безлимит на соцсети', 'featured': False,
     'desc': 'Этот тариф идеально подходит для тех, кто только начинает свой путь в мире мобильной связи: студентов, пенсионеров или пользователей, которым нужен только базовый набор услуг для звонков и мессенджеров. Отличный вариант для малоактивного использования интернета и редких разговоров.'},
    {'name': 'Оптиум',   'price': 499, 'gb': '30 ГБ интернета',  'minutes': '500 минут звонков',  'sms': '100 SMS', 'extra': 'Безлимит на соцсети', 'featured': True,
     'desc': 'Оптимальный выбор для активного современного человека. Подойдёт для повседневной работы, общения, навигации и стриминга музыки. Хватит ресурсов на путешествия по городу, рабочие созвоны и общение с близкими — без оглядки на остатки.'},
    {'name': 'Максимум', 'price': 799, 'gb': '50 ГБ интернета',  'minutes': '800 минут звонков',  'sms': '200 SMS', 'extra': 'Безлимит на соцсети', 'featured': False,
     'desc': 'Тариф для тех, кому связь нужна без компромиссов: командировки, путешествия, удалённая работа из любой точки страны. Полный безлимит на ключевые мессенджеры, повышенные пакеты звонков и интернета — связь, которая всегда поспевает за вами.'},
]

PLAN_DETAILS = {
    'Старт':    {'price': 299, 'gb': 10, 'min': 100, 'sms': 50},
    'Оптиум':   {'price': 499, 'gb': 30, 'min': 500, 'sms': 100},
    'Максимум': {'price': 799, 'gb': 50, 'min': 800, 'sms': 200},
}

SERVICES = [
    {'title': 'Голосовая почта',     'desc': 'Принимайте сообщения когда недоступны',     'price': 'Бесплатно'},
    {'title': 'HD-видео',            'desc': 'Стриминг в высоком качестве без расхода ГБ', 'price': '340 ₽/мес'},
    {'title': 'Безлимит на ночь',    'desc': 'С 23:00 до 7:00 без ограничений',           'price': '99 ₽/мес'},
    {'title': 'Переадресация',       'desc': 'Переадресация на другой номер',             'price': '90 ₽/мес'},
    {'title': 'Дополнительно 10 ГБ', 'desc': 'Разовое пополнение пакета интернета',       'price': '150 ₽'},
    {'title': 'Роуминг Европа',      'desc': 'Звонки и интернет в странах ЕС',            'price': '290 ₽/мес'},
    {'title': 'МКСА ТВ',             'desc': '150+ каналов в Full HD качестве',           'price': '249 ₽/мес'},
]

SEED_REVIEWS = [
    {'name': 'Илья Соболев',  'rating': 5, 'text': 'По работе часто мотаюсь по области и в соседние регионы. С предыдущим оператором вечно была беда: только выезжаешь за МКАД — привет, глухие зоны. Перешёл на MobiWave по совету коллеги (спасибо, Саня!) и офигел. Во-первых, на трассе М4 теперь ловит всегда, можно спокойно подкасты слушать. Во-вторых, в командировке в Ярославле скорость вообще не просела. Очень рад, что дал шанс новому игроку. Тариф «Максимум» — топ за свои деньги.'},
    {'name': 'Марина Волкова', 'rating': 5, 'text': 'Наконец-то нашла оператора, у которого всё работает так, как надо. Пользуюсь пару месяцев — полёт нормальный. Приложение удобное, всё понятно без лишних танцев с бубном. Ребята, молодцы!'},
    {'name': 'Денис Павлов',   'rating': 5, 'text': 'Сначала сомневался, думал очередной виртуал. Оказалось, зря. Связь ловит отлично, проблем нет. Единственное — хотелось бы ещё больше всяких плюшек в будущем. Но старт мощный, 5 баллов.'},
]

if not db.get_reviews():
    for r in SEED_REVIEWS:
        db.add_review(r['name'], r['rating'], r['text'])


class EmailSender:
    SMTP_SERVER = "smtp.gmail.com"
    PORT = 587
    SENDER_EMAIL = "resaromanov@gmail.com"
    PASSWORD = "sgvf tpfb nxop lqbh"

    @classmethod
    def send_payment_email(cls, to_email, payment_data):
        message = f"""
        Спасибо за пополнение счёта MobiWave!

        Ваш платёж:
        Сумма: {payment_data['amount']} ₽
        Способ оплаты: {payment_data['method']}
        ID платежа: {payment_data['id']}

        Средства уже зачислены на ваш счёт.
        """

        msg = MIMEMultipart()
        msg['From'] = cls.SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = "Пополнение счёта MobiWave"
        msg.attach(MIMEText(message, 'plain'))

        try:
            server = smtplib.SMTP(cls.SMTP_SERVER, cls.PORT)
            server.starttls()
            server.login(cls.SENDER_EMAIL, cls.PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False


def login_required():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return None


def validate_json_request(data, required_fields):
    if not data:
        return {'error': 'Нет данных'}, 400
    for field in required_fields:
        if not data.get(field):
            return {'error': f'Заполните поле {field}'}, 400
    return None


def get_authenticated_user():
    user_id = session.get('user_id')
    if not user_id:
        return None, {'error': 'Не авторизован'}, 401
    return user_id, None, None


@app.route('/')
@app.route('/mobiwave/')
@app.route('/mobiwave/home/')
def home():
    return render_template('home.html', reviews=db.get_reviews())


@app.route('/mobiwave/add_review/', methods=['POST'])
def add_review():
    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400

    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    text = (data.get('text') or '').strip()

    try:
        rating = int(data.get('rating', 0))
    except (TypeError, ValueError):
        rating = 0

    if not text:
        return {'error': 'Введите текст отзыва'}, 400
    if not 1 <= rating <= 5:
        return {'error': 'Поставьте оценку от 1 до 5'}, 400

    name = f"{first_name} {last_name}".strip() or session.get('username') or 'Аноним'
    db.add_review(name, rating, text)
    return {'message': 'Отзыв добавлен'}, 200


@app.route('/mobiwave/logout/')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/mobiwave/tariffs/')
def tariffs():
    with_desc = request.args.get('detail') == '1'
    return render_template('tariffs.html', tariffs=TARIFFS, with_desc=with_desc)


@app.route('/mobiwave/services/')
def services_public():
    return render_template('services.html', services=SERVICES)


@app.route('/mobiwave/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    validation_error = validate_json_request(request.get_json(), ['phone', 'password'])
    if validation_error:
        return validation_error

    data = request.get_json()
    user = db.get_user(data['phone'], data['password'])
    if not user:
        return {'error': 'Неверные данные'}, 401

    session['username'] = f"{user['first_name']} {user['last_name']}"
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_phone'] = user['phone']
    return {'message': 'Вход выполнен'}, 200


@app.route('/mobiwave/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    validation_error = validate_json_request(request.get_json(), ['phone', 'email', 'password', 'confirm'])
    if validation_error:
        return validation_error

    data = request.get_json()
    if data['password'] != data['confirm']:
        return {'error': 'Пароли не совпадают'}, 400

    result = db.add_user(
        data.get('first_name', 'Пользователь'),
        data.get('last_name', ''),
        data['phone'],
        data['email'],
        data['password']
    )

    if 'error' in result:
        return result, 400

    session['username'] = f"{data['first_name']} {data['last_name']}".strip()
    session['user_id'] = result['id']
    session['user_email'] = data['email']
    session['user_phone'] = data['phone']
    return {'message': 'Регистрация успешна'}, 200


@app.route('/mobiwave/my_tariff/')
def my_tariff():
    redirect_response = login_required()
    if redirect_response:
        return redirect_response

    user = db.get_user_by_id(session['user_id'])
    plan = user['tariff'] if user and user['tariff'] in PLAN_DETAILS else 'Оптиум'
    return render_template('my_tariff.html', user=user, plan=plan, plan_data=PLAN_DETAILS[plan])


@app.route('/get_payment_history')
def get_payment_history():
    user_id, error_response, status_code = get_authenticated_user()
    if error_response:
        return jsonify(error_response), status_code

    payments = db.get_user_payments(user_id)
    for payment in payments:
        date_value = payment['date']
        if isinstance(date_value, str):
            payment['date'] = date_value
        else:
            payment['date'] = date_value.strftime('%d.%m.%Y %H:%M')

    return jsonify({'payments': payments})


@app.route('/mobiwave/change_tariff/', methods=['POST'])
def change_tariff():
    user_id, error_response, status_code = get_authenticated_user()
    if error_response:
        return error_response, status_code

    data = request.get_json()
    tariff = data.get('tariff')
    if tariff not in PLAN_DETAILS:
        return {'error': 'Неверный тариф'}, 400

    db.update_tariff(user_id, tariff)
    return {'message': 'Тариф изменён'}, 200


@app.route('/mobiwave/dashboard_services/')
def dashboard_services():
    redirect_response = login_required()
    if redirect_response:
        return redirect_response

    active_services = db.get_user_services(session['user_id'])
    return render_template('dashboard_services.html', services=SERVICES, active_services=active_services)


@app.route('/mobiwave/toggle_service/', methods=['POST'])
def toggle_service():
    user_id, error_response, status_code = get_authenticated_user()
    if error_response:
        return error_response, status_code

    data = request.get_json()
    service = data.get('service')
    action = data.get('action')

    if action == 'connect':
        db.connect_service(user_id, service, data.get('price', ''))
    elif action == 'disconnect':
        db.disconnect_service(user_id, service)
    else:
        return {'error': 'Неверное действие'}, 400

    return {'message': 'Готово'}, 200


@app.route('/mobiwave/profile/', methods=['GET', 'POST'])
def profile():
    redirect_response = login_required()
    if redirect_response:
        return redirect_response

    if request.method == 'GET':
        user = db.get_user_by_id(session['user_id'])
        return render_template('profile.html', user=user)

    data = request.get_json()
    result = db.update_profile(
        session['user_id'],
        data.get('first_name'),
        data.get('last_name'),
        data.get('email'),
        data.get('phone')
    )

    if 'error' in result:
        return result, 400

    new_password = data.get('new_password')
    confirm = data.get('confirm_password')
    if new_password:
        if new_password != confirm:
            return {'error': 'Пароли не совпадают'}, 400
        db.update_password(session['user_id'], new_password)

    session['username'] = f"{data.get('first_name')} {data.get('last_name')}".strip()
    session['user_email'] = data.get('email')
    session['user_phone'] = data.get('phone')
    return {'message': 'Профиль обновлён'}, 200


@app.route('/mobiwave/topup/')
def topup():
    redirect_response = login_required()
    if redirect_response:
        return redirect_response

    user = db.get_user_by_id(session['user_id'])
    return render_template('topup.html', user=user)


@app.route('/mobiwave/process_payment/', methods=['POST'])
def process_payment():
    user_id = session.get('user_id')
    if not user_id:
        return {'error': 'Пользователь не авторизован'}, 401

    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400

    payment_data = {
        'id': str(uuid.uuid4())[:8],
        'amount': int(data.get('amount', 0)),
        'method': data.get('method', 'СБП'),
        'user_id': user_id,
        'email': session.get('user_email'),
        'status': 'pending',
    }

    result = db.add_payment(payment_data)
    if 'error' in result:
        return {'error': result['error']}, 500

    threading.Thread(target=_auto_confirm, args=(payment_data['id'],)).start()
    return {'payment_id': payment_data['id'], 'message': 'Платеж создан'}, 200


def _auto_confirm(payment_id):
    import time
    time.sleep(2)

    if db.check_payment(payment_id) == 'pending':
        db.update_payment_status(payment_id, 'confirmed')
        payment = db.get_payment(payment_id)
        if payment:
            db.add_balance(payment['user_id'], payment['amount'])
            if payment['email']:
                EmailSender.send_payment_email(payment['email'], payment)


@app.route('/mobiwave/confirm_payment/', methods=['POST'])
def confirm_payment():
    data = request.get_json()
    if not data:
        return {'error': 'Нет данных'}, 400

    payment_id = data.get('payment_id')
    status = data.get('status')

    current_status = db.check_payment(payment_id)
    if current_status and current_status == 'pending':
        db.update_payment_status(payment_id, status)
        if status == 'confirmed':
            payment = db.get_payment(payment_id)
            if payment:
                db.add_balance(payment['user_id'], payment['amount'])
                if payment['email']:
                    EmailSender.send_payment_email(payment['email'], payment)
        return {'message': f'Платеж {status}'}, 200

    return {'error': 'Платеж не найден или уже обработан'}, 404


@app.route('/mobiwave/payment_status/<payment_id>')
def payment_status(payment_id):
    status = db.check_payment(payment_id)
    return {'status': status if status else 'pending'}


if __name__ == '__main__':
    app.run(debug=True)