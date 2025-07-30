import os
import logging
import csv
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, filename='todo_repository.log', 
                    format='%(asctime)s:%(levelname)s:%(message)s')

class TodoRepository:
    def __init__(self, filename='todos.csv'):
        self.filename = filename
        self.todos = []
        self.load_todos()
    
    def load_todos(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, mode='r', newline='') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        self.todos.append({'task': row[0], 'due_date': row[1], 'completed': row[2] == 'True'})
                logging.info("Todos loaded successfully.")
            except Exception as e:
                logging.error(f"Error loading todos: {e}")

    def save_todos(self):
        try:
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                for todo in self.todos:
                    writer.writerow([todo['task'], todo['due_date'], todo['completed']])
            logging.info("Todos saved successfully.")
        except Exception as e:
            logging.error(f"Error saving todos: {e}")

    def add_task(self, task, due_date):
        try:
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
            self.todos.append({'task': task, 'due_date': due_date_obj.date(), 'completed': False})
            self.save_todos()
            self.send_email_notification(task, due_date)
            logging.info(f"Task added: {task} with due date {due_date}.")
        except Exception as e:
            logging.error(f"Error adding task: {e}")

    def complete_task(self, task):
        try:
            for todo in self.todos:
                if todo['task'] == task and not todo['completed']:
                    todo['completed'] = True
                    self.save_todos()
                    self.send_email_notification(task, 'completed')
                    logging.info(f"Task completed: {task}.")
                    return
            logging.warning(f"Task not found or already completed: {task}.")
        except Exception as e:
            logging.error(f"Error completing task: {e}")

    def send_email_notification(self, task, due_date):
        # Simulated email sending function
        logging.info(f"Sending email notification for task: {task}, due date: {due_date}.")

    def show_todos(self):
        for todo in self.todos:
            status = "✓" if todo['completed'] else "✗"
            logging.info(f"Task: {todo['task']}, Due: {todo['due_date']}, Status: {status}")

def main():
    todo_repo = TodoRepository()
    todo_repo.add_task('Finish the report', '2023-10-10')
    todo_repo.add_task('Call the plumber', '2023-10-11')
    todo_repo.show_todos()
    todo_repo.complete_task('Finish the report')
    todo_repo.show_todos()

if __name__ == "__main__":
    main()