import sqlite3


class database:
    def __init__(self):
        conn = sqlite3.connect('database.db')
        with conn:
            conn.execute(
                '''CREATE TABLE IF NOT EXISTS users
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       first_name TEXT,
                       last_name  TEXT,
                       phone      TEXT UNIQUE,
                       email      TEXT,
                       password   TEXT,
                       tariff     TEXT DEFAULT 'Старт',
                       balance    INTEGER DEFAULT 0
                   )
             ''')

            conn.execute(
                '''CREATE TABLE IF NOT EXISTS payments
                   (
                       id      TEXT PRIMARY KEY,
                       date    DATETIME DEFAULT CURRENT_TIMESTAMP,
                       amount  INTEGER,
                       method  TEXT,
                       user_id INTEGER,
                       email   TEXT,
                       status  TEXT
                   )
             '''
            )

            conn.execute(
                '''CREATE TABLE IF NOT EXISTS user_services
                   (
                       id      INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id INTEGER,
                       service TEXT,
                       price   TEXT,
                       UNIQUE(user_id, service)
                   )
             '''
            )

            conn.execute(
                '''CREATE TABLE IF NOT EXISTS reviews
                   (
                       id     INTEGER PRIMARY KEY AUTOINCREMENT,
                       name   TEXT,
                       rating INTEGER,
                       text   TEXT,
                       date   DATETIME DEFAULT CURRENT_TIMESTAMP
                   )
             '''
            )
        conn.close()

    def get_user_payments(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, date, amount, method, status '
                'FROM payments '
                'WHERE user_id = ? '
                'ORDER BY date DESC, id DESC',
                (user_id,)
            )
            return [
                {
                    'id': row[0],
                    'date': row[1],
                    'amount': row[2],
                    'method': row[3],
                    'status': row[4]
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def get_connection(self):
        return sqlite3.connect('database.db')

    def get_user(self, phone, password):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, first_name, last_name, phone, email, tariff, balance '
                'FROM users '
                'WHERE phone = ? AND password = ?',
                (phone, password)
            )
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'first_name': user[1],
                    'last_name': user[2],
                    'phone': user[3],
                    'email': user[4],
                    'tariff': user[5],
                    'balance': user[6],
                }
            return None
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, first_name, last_name, phone, email, tariff, balance '
                'FROM users WHERE id = ?',
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'first_name': user[1],
                    'last_name': user[2],
                    'phone': user[3],
                    'email': user[4],
                    'tariff': user[5],
                    'balance': user[6],
                }
            return None
        finally:
            conn.close()

    def add_user(self, first_name, last_name, phone, email, password):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO users (first_name, last_name, phone, email, password) '
                'VALUES (?, ?, ?, ?, ?)',
                (first_name, last_name, phone, email, password)
            )
            conn.commit()
            return {'id': cursor.lastrowid, 'message': 'Пользователь успешно добавлен'}
        except sqlite3.IntegrityError:
            return {'error': 'Пользователь с таким номером уже существует'}
        finally:
            conn.close()

    def update_profile(self, user_id, first_name, last_name, email, phone):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE users SET first_name = ?, last_name = ?, email = ?, phone = ? '
                'WHERE id = ?',
                (first_name, last_name, email, phone, user_id)
            )
            conn.commit()
            return {'message': 'Профиль обновлён'}
        except Exception as e:
            return {'error': str(e)}
        finally:
            conn.close()

    def update_password(self, user_id, password):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE users SET password = ? WHERE id = ?',
                (password, user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def update_tariff(self, user_id, tariff):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE users SET tariff = ? WHERE id = ?',
                (tariff, user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def add_balance(self, user_id, amount):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE users SET balance = balance + ? WHERE id = ?',
                (amount, user_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def add_payment(self, payment_data):
        conn = self.get_connection()
        try:
            conn.execute(
                'INSERT INTO payments (id, amount, method, user_id, email, status) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (
                    payment_data['id'],
                    payment_data['amount'],
                    payment_data['method'],
                    payment_data['user_id'],
                    payment_data['email'],
                    payment_data['status'],
                )
            )
            conn.commit()
            return {'message': 'Платеж успешно добавлен'}
        except Exception as e:
            print(f"Ошибка добавления платежа: {e}")
            return {'error': str(e)}
        finally:
            conn.close()

    def check_payment(self, payment_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT status FROM payments WHERE id = ?',
                (payment_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            conn.close()

    def update_payment_status(self, payment_id, status):
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE payments SET status = ? WHERE id = ?',
                (status, payment_id)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def get_payment(self, payment_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, date, amount, method, user_id, email, status '
                'FROM payments WHERE id = ?',
                (payment_id,)
            )
            payment = cursor.fetchone()
            if payment:
                return {
                    'id': payment[0],
                    'date': payment[1],
                    'amount': payment[2],
                    'method': payment[3],
                    'user_id': payment[4],
                    'email': payment[5],
                    'status': payment[6],
                }
            return None
        finally:
            conn.close()

    def get_user_services(self, user_id):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT service FROM user_services WHERE user_id = ?',
                (user_id,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def connect_service(self, user_id, service, price):
        conn = self.get_connection()
        try:
            conn.execute(
                'INSERT OR IGNORE INTO user_services (user_id, service, price) '
                'VALUES (?, ?, ?)',
                (user_id, service, price)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def disconnect_service(self, user_id, service):
        conn = self.get_connection()
        try:
            conn.execute(
                'DELETE FROM user_services WHERE user_id = ? AND service = ?',
                (user_id, service)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def add_review(self, name, rating, text):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO reviews (name, rating, text) VALUES (?, ?, ?)',
                (name, rating, text)
            )
            conn.commit()
            return {'id': cursor.lastrowid}
        finally:
            conn.close()

    def get_reviews(self):
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT id, name, rating, text FROM reviews ORDER BY date DESC, id DESC'
            )
            return [
                {'id': r[0], 'name': r[1], 'rating': r[2], 'text': r[3]}
                for r in cursor.fetchall()
            ]
        finally:
            conn.close()


db = database()
