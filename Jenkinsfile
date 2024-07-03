pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                script{
                    sh 'docker cp tg_bot_free:/app/users /DATA/Downloads/users_get'
                }
                // Проверка кода из вашего репозитория
                git branch: 'main', 
                    url: 'https://github.com/Edge0fSanity/Tg_bot_free.git'
            }
        }
        /*
        stage('Install Dependencies') {
            steps {
                // Установка зависимостей
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Run Tests') {
            steps {
                // Запуск тестов
                echo "Тестов нет"
            }
        }
        */
        stage('Build Docker Image') {
            steps {
                script{
                    // Построение Docker-образа
                    docker.build('tg_bot_free')
                }
            }
        }
        stage('Deploy') {
            steps {
                // Удаление старого контейнера
                sh 'docker rm -f tg_bot_free || true'
                // Развертывание Docker-контейнера
                sh 'docker run -d --name tg_bot_free tg_bot_free:latest'
                // Копирование файлов пользователей
                sh 'docker cp /DATA/Downloads/users_get/users tg_bot_free:/app'
                
                sh 'docker exec tg_bot_free chown -R appuser /app'
            }
        }
    }
    post {
        always {
            // Действия, которые выполняются всегда, независимо от успешности выполнения этапов
            cleanWs()
        }
        success {
            // Действия, которые выполняются только в случае успешного выполнения всех этапов
            echo 'Pipeline succeeded!'
        }
        failure {
            // Действия, которые выполняются только в случае неуспешного выполнения любого из этапов
            echo 'Pipeline failed!'
        }
    }
}
