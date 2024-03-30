import os
import time
from playwright.sync_api import sync_playwright, TimeoutError
import random
import string
from loguru import logger
import multiprocessing
from settings import num_threads, headless

def gen_random_sequence(length):
    random_sequence = ''.join(random.choice(string.ascii_letters) for _ in range(length))
    return random_sequence

def complete_first_step(page, now_file):
    page.check('input[type="checkbox"][name="terms"]')
    page.fill('input[name="mobile"]', '027'+str(random.randint(1000000, 9999999)))
    page.press('input[name="mobile"]', 'Enter')
    page.select_option('select[name="shapes_product"]', value='Other')
    page.select_option('select[name="retailer"]', value='Countdown/Woolworths')
    page.select_option('select[name="online"]', value='No')
    submit_file(page, now_file)


def submit_file(page, now_file):
    page.focus('#receipt_upload')
    page.click('#receipt_upload')
    page.set_input_files('#receipt_upload', f'/home/vanusha/temp_project/photos/{now_file}')
    time.sleep(5)
    page.click('css=button[type="button"]')
    time.sleep(2)
    page.set_input_files('#receipt_upload', f'/home/vanusha/temp_project/photos/{now_file}')
    time.sleep(5)
    page.click('css=button[type="submit"]')


def complete_second_step(page, mail, addresses, names, cities, surnames):
    page.fill('input[name="first_name"]', random.choice(names))
    time.sleep(2)
    page.fill('input[name="last_name"]', random.choice(surnames))
    time.sleep(2)
    page.fill('input[name="email"]', mail)
    time.sleep(1)
    page.fill('input[name="confirm_email"]', mail)
    time.sleep(1)
    page.fill('input[name="address_line_1"]', random.choice(addresses))
    time.sleep(1)
    page.fill('input[name="suburb"]', random.choice(cities))
    time.sleep(1)
    page.select_option('select[name="state"]', value='Gisborne')
    time.sleep(1)
    page.fill('input[name="postcode"]', str(random.randint(1000, 9999)))
    time.sleep(1)
    page.check('input[type="checkbox"][name="over_eighteen"]')
    page.check('input[type="checkbox"][name="marketing"]')
    page.check('input[type="checkbox"][name="privacy"]')
    time.sleep(3)
    page.click('css=button[type="submit"]')


def runner(mail, my_name, proxies, addresses, names, cities, surnames):
    proxy = random.choice(proxies)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, proxy={
            "server": f'{proxy["host"]}:{proxy["port"]}',
            "username": proxy['username'],
            "password": proxy['password']
        })
        page = browser.new_page()
        try:
            page.goto('https://www.shapeswin.com/nz')
        except TimeoutError:
            logger.warning(f'Процесс {my_name}: Сайт не загрузился (проксики косячит)')
            return
        logger.info(f'Процесс {my_name}: Перешел на сайт')
        try:
            now_file = random.choice([x for x in os.listdir('./photos') if x.endswith('.jpg')])
            complete_first_step(page, now_file)
        except TimeoutError:
            logger.warning(f'Процесс {my_name}: Ошибка при заполнение форму, попробую еще раз не удаляя почту')
        else:
            os.remove(f'./photos/{now_file}')
            expected_text = 'CONTACT DETAILS'
            try:
                time.sleep(15)
                page.wait_for_function(f'document.querySelector("h1").innerText.includes("{expected_text}")', timeout=5000)
            except TimeoutError:
                logger.warning(f'Процесс {my_name}: Ошибка при заполнение форму, попробую еще раз не удаляя почту')
            else:
                logger.info(f'Процесс {my_name}: Завершил первый этап')
                complete_second_step(page, mail, addresses, names, cities, surnames)
                logger.info(f'Процесс {my_name}: Завершил второй этап')
                remove_processed_emails(mail)
                add_email(mail)
                logger.info(f'Процесс {my_name}: Все прошло успешно, почта {mail}')
                time.sleep(15)
                # expected_text = 'CONGRATS'
                # try:
                #     time.sleep(15)
                # except TimeoutError:
                #     logger.error(f'Процесс {my_name}: Удаляю почту победа не обнаружена')
                #     remove_processed_emails(mail)
                # else:


def add_email(email_to_remove):
    with open('./output_file.txt', 'a+') as output_file:
        output_file.write('\n'+email_to_remove)


def remove_processed_emails(email_to_remove):
    with open('./input_file.txt', 'r') as input_file_read:
        lines = input_file_read.readlines()

    with open('./input_file.txt', 'w') as input_file_write:
        for line in lines:
            email = line.strip().split(':')[0]
            if email not in email_to_remove:
                input_file_write.write(line)


def complete_all(lines, proxies, addresses, names, cities, surnames):
    processes = []
    for line in lines:
        mail = line.strip()
        process = multiprocessing.Process(target=runner, args=(mail, len(processes), proxies, addresses, names, cities, surnames))
        processes.append(process)
        process.start()

        if len(processes) >= num_threads:
            for process in processes:
                process.join()
            processes = []
    for process in processes:
        process.join()


if __name__ == '__main__':
    lines = True
    with open('./proxy.txt', 'r') as file:
        proxies = file.readlines()
        proxies = [i[:-1].split(':') for i in proxies]
        proxies = [{'host': i[0], 'port': i[1], 'username': i[2], 'password': i[3]} for i in proxies]
    with open('./address.txt', 'r') as file:
        addresses = file.readlines()
        addresses = [i[:-1] for i in addresses]
    with open('./names.txt', 'r') as file:
        names = file.readlines()
        names = [i[:-1] for i in names]
    with open('cities.txt', 'r') as file:
        cities = file.readlines()
        cities = [i[:-1] for i in cities]
    with open('./Surnames.txt', 'r') as file:
        surnames = file.readlines()
        surnames = [i[:-1] for i in surnames]
    while lines:
        with open('./input_file.txt', 'r') as file:
            lines = file.readlines()
        complete_all(lines, proxies, addresses, names, cities, surnames)