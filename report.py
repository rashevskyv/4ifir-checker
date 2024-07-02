from aiogram import Bot, types
import os
from status_result import process_items
from datetime import datetime
import shutil
from settings import TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID, report_file

bot_token, chat_id, message_thread_id = TELEGRAM_BOT_TOKEN, YOUR_CHAT_ID, TOPIC_ID

def create_html_report(results, last_modified):
    report_content = ''

    if all(not items for items in results.values()):
        return report_content
    
    # report_content += f'<h2>Archive Comparison Report for <b>{archive_filename}</b></h2>\n\n'
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
            # print(f"======================\nfolder_tree for {archive_filename}:\n======================\n\n{folder_tree}")
            report_content += render_tree(folder_tree)
            report_content += '</pre>\n'
            # print(str(report_content))
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
    # Генерування закриваючого тегу
    close_tag = tag.replace('<', '</')

    # Зменшення max_length на розмір tag + close_tag
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
        # print(f"block: {block}\n---------------------\n\n")

        # Перевірка блоку на наявність tag та close_tag
        start_tag = "<b>"


        if not block.startswith(start_tag):
            block = tag + block
        tag_count = block.count(tag)
        close_tag_count = block.count(close_tag)
        if tag_count != close_tag_count:
            block += close_tag

        # print(f"block after tag check: {block}\n---------------------\n\n")

        blocks.append(block)
        start_index = end_index

    return header, blocks

async def send_to_tg(report_content, file, archivename):
        
    def process_report_content(report_content):
        report_content = report_content.replace("<h2>", "<b>").replace("</h2>", "</b>\n").replace("<h3>", "<b>").replace("</h3>", "</b>\n").replace("<br>", "\n").replace("<hr>", "\n-------------------------------")
        # print(f"======================\nreport_content for {archivename}:\n======================\n\n{report_content}\n====--------------====\n\n")
        header, blocks = split_html_content(report_content)
        # print("header:", header)
        # print(f"======================\nblocks for {archivename}:\n======================\n\n{blocks}\n====--------------====\n\n")
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

    # Если размер хедера больше 900 символов
    if len(header) > 900:
        split_index = header.rfind("</pre>") + len("</pre>")
        first_part = header[:split_index]
        second_part = header[split_index:]

        if len(first_part) < 1024:
            # Отправляем файл с описанием (first_part)
            await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=first_part, parse_mode=types.ParseMode.HTML)
            # Check if the second_part is larger than 4000 characters
            if len(second_part) > 4000:
                # Split the second_part into smaller parts
                parts = []
                start = 0
                while start < len(second_part):
                    end = second_part.rfind('</pre>', start, start + 4000) + len('</pre>')
                    if end == -1 + len('</pre>'):
                        end = len(second_part)
                    parts.append(second_part[start:end])
                    start = end

                # Send the smaller parts of the second_part
                for i, part in parts:
                    # print("Sending header if message bigger than 4K...")
                    # print(f"Part {i} of {len(parts)}: {part}\n---------------------\n\n")
                    await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)
            else:
                # Отправляем вторую часть
                print("Sending body if message bigger than 4K...")
                await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=second_part, parse_mode=types.ParseMode.HTML)
        else:
            # Отправляем обе части одним сообщением
            print("Sending both parts of the header if message text smaller than 4K...")
            await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=small_caption, parse_mode=types.ParseMode.HTML)
            await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=headless_header, parse_mode=types.ParseMode.HTML)
    else:
        # Отправляем файл с описанием (header)
        print("Sending header if message smaller than 4K...")
        # print(f"Header: {header}\n---------------------\n\n")
        await bot.send_document(chat_id=chat_id, message_thread_id=message_thread_id, document=file_obj, caption=header, parse_mode=types.ParseMode.HTML)
        print("DONE")

    # Отправляем блоки содержимого
    for part in blocks:
        print("Sending body if message smaller than 4K...")
        # print(f"{part}\n---------------------\n\n")
        await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=part, parse_mode=types.ParseMode.HTML)

    file_obj.close()    
    await bot.close()

async def send_tg_message(message):
    bot = Bot(token=bot_token)
    print("Sending message to Telegram...")
    await bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=message)
    print("Message sent to Telegram.")
    await bot.close()
