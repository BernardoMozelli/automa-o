import psutil
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchWindowException,
    NoSuchElementException
)
import time  # Para pausas curtas, se necessário

# Inicializa o WebDriver (no caso, Chrome)
driver = webdriver.Chrome()

# Abre a página de login
driver.get("https://santaluzia-mg.nobesistemas.com.br/saude/screening_attendance_panels")

def login():
    try:
        # Espera o campo de usuário estar visível
        wait = WebDriverWait(driver, 10)
        username_input = wait.until(EC.presence_of_element_located((By.ID, "user_login")))

        # Envia o nome de usuário
        username_input.send_keys("paineladulto")

        # Encontra o campo de senha e insere a senha
        password_input = driver.find_element(By.CSS_SELECTOR, 'input[type="password"]')
        password_input.send_keys("123456")

        # Encontra o botão de submissão
        submit_button = driver.find_element(By.NAME, "commit")

        try:
            # Tenta clicar no botão normalmente
            submit_button.click()
        except ElementClickInterceptedException:
            # Caso o clique seja interceptado, tenta rolar até o botão e clicar via JavaScript
            print("Elemento não está clicável diretamente, rolando e forçando o clique via JavaScript.")
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            driver.execute_script("arguments[0].click();", submit_button)

        # Adiciona algum tempo de espera para carregar a próxima página
        WebDriverWait(driver, 10).until(EC.url_changes('https://santaluzia-mg.nobesistemas.com.br/saude/users/sign_in'))

        # Redireciona para a URL desejada após o login
        driver.get("https://santaluzia-mg.nobesistemas.com.br/saude/screening_attendance_panels")

        # Maximiza a janela do navegador
        driver.fullscreen_window()  # Alternativa ao modo F11

        # Adiciona um evento para impedir o fechamento da página
        driver.execute_script("""
            window.onbeforeunload = function() {
                return 'Você tem certeza que deseja sair?';
            };
        """)

        # Adiciona SweetAlert ao DOM
        driver.execute_script("""
            var script = document.createElement('script');
            script.src = 'https://unpkg.com/sweetalert/dist/sweetalert.min.js';
            document.head.appendChild(script);
        """)

        # Aguarda o carregamento do script SweetAlert
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return typeof swal !== 'undefined'"))

        # Exibe um alerta de sucesso e o fecha após 4 segundos
        driver.execute_script("""
            swal('**Importante**', 'Favor não fechar o navegador!!!', 'info');
            setTimeout(function() {
                swal.close();
            }, 4000);  // 4000 milissegundos = 4 segundos
        """)

    except TimeoutException:
        return False

    return True

def check_authentication():
    try:
        # Verifica se algum elemento específico da página autenticada está presente
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_submit")))
        return True
    except (TimeoutException, NoSuchElementException):
        print("Autenticação falhou.")
        return False
    except NoSuchWindowException:
        print("A janela do navegador foi fechada. Encerrando o script.")
        return False

def is_logged_out():
    try:
        # Verifica se o navegador foi redirecionado para a página de login
        current_url = driver.current_url
        return current_url == "https://santaluzia-mg.nobesistemas.com.br/saude/users/sign_in"
    except NoSuchWindowException:
        print("A janela do navegador foi fechada durante a verificação de logoff.")
        return False

def check_empty_bookmark():
    try:
        # Verifica se o navegador está na página de bookmark vazia
        current_url = driver.current_url
        if current_url == "https://santaluzia-mg.nobesistemas.com.br/saude/bookmark/empty":
            print("Estando na página de bookmark vazio. Redirecionando para a página principal...")
            driver.get("https://santaluzia-mg.nobesistemas.com.br/saude/child_attendance_panels")
            return True
        return False
    except NoSuchWindowException:
        print("A janela do navegador foi fechada durante a verificação da página de bookmark.")
        return False

def reauthenticate():
    attempts = 0
    max_attempts = 3  # Número máximo de tentativas de autenticação
    while attempts < max_attempts:
        print(f"Tentando autenticar novamente... (Tentativa {attempts + 1}/{max_attempts})")
        if login() and check_authentication():
            print("Reautenticação bem-sucedida.")
            return True
        attempts += 1
        print("Reautenticação falhou. Tentando novamente...")

    print("Número máximo de tentativas de reautenticação alcançado.")
    return False

try:
    # Tenta fazer o login
    if login():
        # Verifica se está autenticado
        if not check_authentication():
            print("Tentativa de autenticação falhou após login.")
            # Tenta reautenticar
            reauthenticate()
        
        # Monitora a sessão continuamente para detectar logoff e reautenticar de forma instantânea
        while True:
            try:
                # Verifica se foi redirecionado para a página de login
                if is_logged_out():
                    print("Sessão expirada ou redirecionado para a página de login. Tentando reautenticar...")
                    if not reauthenticate():  # Tenta reautenticar e verifica se a reautenticação foi bem-sucedida
                        print("Reautenticação falhou. Encerrando o script.")
                        break
                
                # Verifica se está na página de bookmark vazia
                if check_empty_bookmark():
                    driver.fullscreen_window()  # Alternativa ao modo F11
                    continue  # Se redirecionou, continua a verificação

                # Aguardando brevemente para evitar sobrecarga de CPU, mas não impede a instantaneidade
                time.sleep(0.5)  # Reduzido para 0.5 segundos para uma resposta mais rápida

            except NoSuchWindowException:
                print("A janela do navegador foi fechada. Encerrando o script.")
                break  # Sai do loop se a janela foi fechada

finally:
    try:
        driver.quit()  # Fecha o navegador ao final
    except NoSuchWindowException:
        print("A janela já foi fechada.")
