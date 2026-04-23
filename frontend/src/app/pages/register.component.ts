import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms'; 

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
export class RegisterComponent {
  registrationData = {
    username: '',
    password: '',
    email: ''
  };

  constructor(private http: HttpClient) {}

  onRegister() {
    const apiUrl = 'http://127.0.0.1:8000/api/register/';
    
    console.log('Отправляем данные:', this.registrationData);

    this.http.post(apiUrl, this.registrationData).subscribe({
      next: (response) => {
        alert('Регистрация прошла успешно! Теперь ты в базе KBTU Chess.');
        console.log('Ответ сервера:', response);
      },
      error: (error) => {
        console.error('Ошибка регистрации:', error);
        alert('Что-то пошло не так. Проверь консоль или спроси коллегу про CORS.');
      }
    });
  }
}