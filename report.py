from aiogram import Bot, types
import os
from status_result import process_items
from datetime import datetime
import shutil
from settings import TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID, report_file, TELEGRAM_API_HASH, TELEGRAM_API_ID, TELEGRAM_USERNAME
from telethon import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import InputMediaUploadedDocument
from tqdm import tqdm  # Імпортуємо tqdm для прогрес бару

bot_token, chat_id, message_thread_id = TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID

def create_html_report(results, last_modified):
    report_content = ''

    if all(not items for items in results.values()):
        return report_content
    
    formatted_last_modified = datetime.fromisoformat(last_modified).strftime('%d.%m.%Y %H:%M')
    report_content += f'<b>Last archive modification date:</b> {formatted_last_modified}<hr>\n\n'
    
    for change_type, items in results.items():
        if items:
            if change_type == "added":
                report_content += '<h3>Added files/folders</h3>\n<pre>'
            elif change_type == "removed":
                report_content += '<h3>Removed files/folders</h3>\n<pre>'
            elif change_type == "modified":
                report_content += '<h3>Modified files</h3>\n<pre>'
            folder_tree = process_items(items)
            report_content += render_tree(folder_tree)
            report_content += '</pre>\n'
    return report_content

def render_tree(tree, level=0, prefix=''):
    tree_str = ""
    items = list(tree.items())
    
    for i, (key, value) in enumerate(items):
        is_last = i == len(items) - 1
        current_prefix = prefix
        
        if level > 0:
            current_prefix += '└╴' if is_last else '├╴'
        
        if isinstance(value, dict):
            tree_str += f"{current_prefix}{key}\n"
            new_prefix = prefix
            if level > 0:
                new_prefix += '  ' if is_last else '│ '
            tree_str += render_tree(value, level + 1, new_prefix)
        else:
            if "(" in value and ")" in value:
                file_name, checksum = value.split('(')
                checksum_short = checksum[1:8]
                
                if len(file_name) > 30:
                    file_name = file_name[:15] + "..." + file_name[-15:]
                
                tree_str += f"{current_prefix}{file_name}({checksum_short})\n"
            else:
                tree_str += f"{current_prefix}{value}\n"
    
    return tree_str

def split_html_content(content, max_length=4096, tag='<pre>', delimiter='-------------------------------'):
    close_tag = tag.replace('<', '</')
    max_length -= len(tag) + len(close_tag)

    content_length = len(content)
    if content_length <= max_length:
        return content, []

    header_end_index = content.find(delimiter)
    if header_end_index != -1:
        header = content[:header_end_index + len(delimiter)]
        content = content[header_end_index + len(delimiter):]
        content_length = len(content)
    else:
        header = ''

    blocks = []
    start_index = 0

    while start_index < content_length:
        end_index = start_index + max_length
        if end_index < content_length:
            end_index = content.rfind('\n', start_index, end_index)
            if end_index == -1:
                end_index = start_index + max_length

        block = content[start_index:end_index].strip()
        if not block.startswith("<b>"):
            block = tag + block
        tag_count = block.count(tag)
        close_tag_count = block.count(close_tag)
        if tag_count != close_tag_count:
            block += close_tag

        blocks.append(block)
        start_index = end_index

    return header, blocks

async def send_large_file_with_telethon(file_path, reply_to_message_id):
    """Функція для відправки великих файлів за допомогою Telethon з прогрес баром."""
    client = TelegramClient('session_name', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()

    try:
        # Спроба отримати об'єкт чату через chat_id
        try:
            chat = await client.get_input_entity(chat_id)
        except ValueError as e:
            print(f"Помилка при отриманні об'єкта чату через ID: {e}")
            # Якщо не вдалося через ID, спробуємо через username
            try:
                chat = await client.get_input_entity(TELEGRAM_USERNAME)
                print(f"Використовується username: {TELEGRAM_USERNAME}")
            except ValueError as e:
                print(f"Помилка при отриманні об'єкта чату через username: {e}")
                return

        # Відкриваємо файл для читання
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as file:
            # Використовуємо tqdm для відображення прогресу
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Завантаження файлу") as pbar:
                # Завантажуємо файл частинами
                uploaded_file = await client.upload_file(
                    file,
                    progress_callback=lambda sent, total: pbar.update(sent - pbar.n)
                )
        
        # Відправляємо файл у відповідь на повідомлення
        await client.send_file(
            chat,
            file=uploaded_file,
            # caption="Великий файл, відправлено через Telethon",
            reply_to=reply_to_message_id  # Відповідь на повідомлення
        )
        print(f"\nФайл {file_path} успішно відправлено через Telethon.")
    except Exception as e:
        print(f"\nПомилка при відправці файлу через Telethon: {e}")
    finally:
        await client.disconnect()

async def send_to_tg(report_content, file, archivename):
    def process_report_content(report_content):
        report_content = report_content.replace("<h2>", "<b>").replace("</h2>", "</b>\n").replace("<h3>", "<b>").replace("</h3>", "</b>\n").replace("<br>", "\n").replace("<hr>", "\n-------------------------------")
        header, blocks = split_html_content(report_content)
        delimiter="-------------------------------"
        split_index = header.rfind(delimiter)
        small_caption = header[:split_index]
        headless_header=header[split_index+len(delimiter):]
        return header, blocks, small_caption, headless_header

    def prepare_file(file, archivename):
        desired_filename = archivename + '.zip'
        if file != desired_filename:
            shutil.copy2(file, desired_filename)
        file_obj = open(desired_filename, 'rb')
        return file_obj

    header, blocks, small_caption, headless_header = process_report_content(report_content)
    file_obj = prepare_file(file, archivename)

    bot = Bot(token=bot_token)

    desired_filename = archivename + '.zip'
    if file != desired_filename:
        shutil.copy2(file, desired_filename)
    file_obj = open(desired_filename, 'rb')

    # Перевірка розміру файла
    file_size = os.path.getsize(desired_filename)
    max_file_size = 49 * 1024 * 1024  # 49 МБ у байтах

    first_message_id = None  # Змінна для збереження ID першого повідомлення

    if file_size > max_file_size:
        print(f"File {desired_filename} is too large ({file_size} bytes). Sending message without file.")
        if len(header) > 900:
            split_index = header.rfind("</pre>") + len("</pre>")
            first_part = header[:split_index]
            second_part = header[split_index:]

            if len(first_part) < 1024:
                sent_message = await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=first_part, parse_mode=types.ParseMode.HTML)
                if first_message_id is None:  # Зберігаємо ID першого повідомлення
                    first_message_id = sent_message.message_id
                if len(second_part) > 4000:
                    parts = []
                    start = 0
                    while start < len(second_part):
                        end = second_part.rfind('</pre>', start, start + 4000) + len('</pre>')
                        if end == -1 + len('</pre>'):
                            end = len(second_part)
                        parts.append(second_part[start:end])
                        start = end

                    for part in parts:
                        await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)
                else:
                    await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=second_part, parse_mode=types.ParseMode.HTML)
            else:
                sent_message = await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=small_caption, parse_mode=types.ParseMode.HTML)
                if first_message_id is None:  # Зберігаємо ID першого повідомлення
                    first_message_id = sent_message.message_id
                await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=headless_header, parse_mode=types.ParseMode.HTML)
        else:
            sent_message = await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=header, parse_mode=types.ParseMode.HTML)
            if first_message_id is None:  # Зберігаємо ID першого повідомлення
                first_message_id = sent_message.message_id

        for part in blocks:
            await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)

        # Відправка великого файлу через Telethon
        if first_message_id is not None:
            await send_large_file_with_telethon(desired_filename, first_message_id)
    else:
        if len(header) > 900:
            split_index = header.rfind("</pre>") + len("</pre>")
            first_part = header[:split_index]
            second_part = header[split_index:]

            if len(first_part) < 1024:
                sent_message = await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=first_part, parse_mode=types.ParseMode.HTML)
                if first_message_id is None:  # Зберігаємо ID першого повідомлення
                    first_message_id = sent_message.message_id
                if len(second_part) > 4000:
                    parts = []
                    start = 0
                    while start < len(second_part):
                        end = second_part.rfind('</pre>', start, start + 4000) + len('</pre>')
                        if end == -1 + len('</pre>'):
                            end = len(second_part)
                        parts.append(second_part[start:end])
                        start = end

                    for part in parts:
                        await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)
                else:
                    await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=second_part, parse_mode=types.ParseMode.HTML)
            else:
                sent_message = await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=small_caption, parse_mode=types.ParseMode.HTML)
                if first_message_id is None:  # Зберігаємо ID першого повідомлення
                    first_message_id = sent_message.message_id
                await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=headless_header, parse_mode=types.ParseMode.HTML)
        else:
            sent_message = await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=header, parse_mode=types.ParseMode.HTML)
            if first_message_id is None:  # Зберігаємо ID першого повідомлення
                first_message_id = sent_message.message_id

        for part in blocks:
            await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)

    file_obj.close()    
    session = await bot.get_session()  # Отримуємо сесію через get_session()
    await session.close()  # Закриваємо сесію

    # Виведення ID першого повідомлення
    if first_message_id is not None:
        print(f"ID першого повідомлення: {first_message_id}")

async def send_tg_message(message):
    bot = Bot(token=bot_token)
    print("Sending message to Telegram...")
    sent_message = await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=message, parse_mode=types.ParseMode.HTML)
    print(f"Message sent to Telegram. ID повідомлення: {sent_message.message_id}")
    session = await bot.get_session()  # Отримуємо сесію через get_session()
    await session.close()  # Закриваємо сесію