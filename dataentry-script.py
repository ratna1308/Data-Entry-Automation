from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

def start_explorer():
    try:
        driver = webdriver.Chrome()
        return driver
    except WebDriverException:
        input("ChromeDriver is not installed on your PC. Press 'ENTER' to install...")
        print("Installing ChromeDriver...")
        return webdriver.Chrome(ChromeDriverManager().install())

def select_option(id_menu, value):
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, id_menu)))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, id_menu)))
        menu = driver.find_element(By.ID, id_menu)
        select = Select(menu)
        select.select_by_value(value)

    except Exception as e:
        print(f"Error selecting option at menu '{id_menu}': {e}")
        input()

def process_questions():

    question_number = 0

    def upload_question(question_data):

        try:
            print(f"Ingresando datos de pregunta {question_number}")

            # Difficulty level is set by question number and adapted to corresponding value in html menu
            # Questions 1-5 are Básico, 5-10 are Intermedio and the rest Advanced
            if question_number <= 5:
                diff = "1"
            elif question_number <= 10:
                diff = "2"
            else:
                diff = "3"

            # Click on difficulty level menu and enter corresponding value
            menu = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "(//select[@id='level_id'])[2]")))
            select = Select(menu)
            select.select_by_value(diff)

            # Fill question field
            question_field = driver.find_elements(By.CLASS_NAME, "note-editable")[0]
            action = ActionChains(driver)
            action.click(question_field).send_keys(question_data['question']).perform()

            # Select type of question by quantity of answers
            # Only one correct answer is a "radio" question (value 3 in html menu)
            # Multiple correct answers is a "checkbox" (value 1 in html menu)
            type = "3" if len(question_data['correct_answer']) == 1 else "1"
            select_option('type_id', type)

            # Select topic (not relevant, always the same. In this case the third one)
            select_option('topic_id', '3')

            # Fill question points (always 10)
            points = driver.find_elements(By.ID, "points")
            points[1].send_keys("10")

            # Select quantity of answers
            answers_count = str(len(question_data['answers']))
            select_option('cant_questions', answers_count)

            # Upload answers and check the correct/s one/s box
            for i, answer in enumerate(question_data['answers'], start=1):
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, f"answer[{i}]text")))
                driver.find_element(By.NAME, f"answer[{i}]text").send_keys(answer)
                # Check if current question is correct
                if i in question_data['correct_answer']:
                    driver.find_element(By.NAME, f"is_correct[{i}]correct").click()
            
            # Fill explanation field, if existing
            if 'explanation' in question_data:
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "explicacion")))
                driver.find_element(By.ID, "explicacion").send_keys(question_data['explanation'])

            # Fill objectives field (always 1)
            driver.find_element(By.ID, "objetivos").send_keys("1")

            # Save the question
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            save_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Guardar')]")
            driver.execute_script("arguments[0].click();", save_button)

            print(f"Pregunta {question_number} cargada con éxito.")

            # Click on new question checkbox to leave all fields shown and ready for next question
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

        except Exception as e:
            print(f"Error al procesar pregunta {question_number}: {e}")
            input()

    # Open file and process each line
    with open(f"{exam}.txt", 'r', encoding='utf-8') as file:
        question_data = {}
        answers = []
        question_data['correct_answer'] = []
        for line in file:
            line = line.strip()
            # Check if line is a question (Format: Pregunta 1: ...). 
            # Beginning of data extraction
            if line.startswith('Pregunta'):
                question_number += 1
                question_data = {}
                answers = []
                question_data['correct_answer'] = []
                # Extract question
                question_data['question'] = line.split(":", 1)[1].strip()
            
            # Check if line is an answer (Format: A) B) C) etc.), ignoring correct answer to avoid duplicate answers
            # Check if answer is correct or incorrect, and delete that information
            # Add answer to answers list

            elif ')' in line and len(line.split(')')[0]) == 1 and not line.startswith('Opción correcta:'):
                _, clean_answer = line.split(')', 1)
                if "(Respuesta correcta)" in clean_answer:
                    question_data['correct_answer'] = len(answers) + 1
                    clean_answer = clean_answer.replace("(Respuesta correcta)", "").strip()
                elif "(Respuesta incorrecta)" in clean_answer:
                    clean_answer = clean_answer.replace("(Respuesta incorrecta)", "").strip()
                answers.append(clean_answer.strip())
            
            # Check if line is an answer (Format: 1. 2. 3. etc.), ignoring correct answer to avoid duplicate answers
            # Check if answer is correct or incorrect, and delete that information
            # Add answer to answers list
            elif '.' in line and line.strip().split('.')[0].isdigit():
                _, clean_answer = line.split('.', 1)
                if "(Respuesta correcta)" in clean_answer:
                    question_data['correct_answer'].append(len(answers) + 1)
                    clean_answer = clean_answer.replace("(Respuesta correcta)", "").strip()
                elif "(Respuesta incorrecta)" in clean_answer:
                    clean_answer = clean_answer.replace("(Respuesta incorrecta)", "").strip()
                answers.append(clean_answer.strip())
        
            # Check if line is a correct answer (can be multiple correct answers) with format (Opción correcta: A) B) C) etc. or 1. 2. 3. etc.)
            elif line.startswith('Opción correcta:'):
                try:
                    correct_answer_letter = line.split(':')[1].split(")")[0].lower().strip()
                    correct_answer_index = 'abcdefgh'.index(correct_answer_letter) + 1
                    question_data['correct_answer'].append(correct_answer_index)
                except:
                    correct_answer_number = line.split(':')[1].split(")")[0].strip()
                    question_data['correct_answer'].append(int(correct_answer_number))
            
            # Check if line is an explanation (Format: Explicación: ...)
            elif line.startswith('Explicación:'):
                question_data['explanation'] = line.split(':', 1)[1].strip()
            
            # End of current question, update question data with the answers and call to upload question function 
            elif line.startswith('!'):
                question_data['answers'] = answers
                upload_question(question_data)

# Program start and request of URL and file with questions
url = input("Hola\nPegá acá el link donde tenés que cargar las preguntas: ")
exam = input("Ahora escribí tal cual el nombre del archivo (sin el '.txt') que tiene el examen: ")

while exam:
    try:
        file_check = open(f"{exam}.txt", "r")
        file_check.close()
        break
    except:
        exam = input("No encuentro el archivo, fijate que esté guardado en la misma carpeta que este programa y que esté en formato '.txt'\nPoné de nuevo el nombre (corroborá que esté escrito tal cual, y sin el '.txt' al final): ")

try:
    driver = start_explorer()
    driver.get(url)
    driver.maximize_window()

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "username"))).send_keys("# USER LOGIN CREDENTIALS")
    driver.find_element(By.ID, "password").send_keys("# USER LOGIN CREDENTIALS")
    driver.find_element(By.ID, "loginButton").click()

    driver.get(url)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "new_question"))).click()

    process_questions()

except Exception as e:
    print(f"Se ha producido un error: {e}")

finally:
    input("Se cargaron todas las preguntas\nApretá ENTER para cerrar el programa.\n")
    driver.quit()