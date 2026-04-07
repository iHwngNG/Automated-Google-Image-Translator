import asyncio
import os
import shutil
from typing import Callable
from playwright.async_api import async_playwright

async def translate_worker(
    worker_id: int,
    queue: asyncio.Queue,
    context,
    output_folder: str,
    sl: str,
    tl: str,
    log_callback: Callable[[str], None],
    app_state: dict,
):
    while True:
        if app_state.get("stop"):
            break
            
        while app_state.get("pause"):
            await asyncio.sleep(0.5)
            if app_state.get("stop"):
                break
                
        if app_state.get("stop"):
            break

        image_path = await queue.get()
        if image_path is None:
            # Poison pill to stop worker
            queue.task_done()
            break

        filename = os.path.basename(image_path)
        log_callback(f"[Worker {worker_id}] Bắt đầu dịch: {filename}")

        page = None
        try:
            page = await context.new_page()
            url = f"https://translate.google.com/?sl={sl}&tl={tl}&op=images&hl=en"

            # Navigate and wait for structural load
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Locate and upload image via robust role/accessibility selector
            file_input = page.get_by_role("button", name="Browse your files").first
            await file_input.wait_for(state="visible", timeout=30000)

            async with page.expect_file_chooser() as fc_info:
                await file_input.click()
            file_chooser = await fc_info.value
            await file_chooser.set_files(image_path)

            log_callback(f"[Worker {worker_id}] Đã tải ảnh lên ({filename}), đang chờ kết quả dịch...")

            # Wait for download button via robust selector
            download_button = page.get_by_role("button", name="Download translation").first
            await download_button.wait_for(state="visible", timeout=60000)

            # Trigger download and verify
            async with page.expect_download() as download_info:
                await download_button.click()
            download = await download_info.value

            output_path = os.path.join(output_folder, filename)
            await download.save_as(output_path)

            log_callback(f"[Worker {worker_id}] Thành công: {filename} -> Lưu tại {output_folder}")
        except Exception as e:
            log_callback(f"[Worker {worker_id}] Lỗi khi dịch {filename}: {str(e)}")
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
            queue.task_done()

async def process_images(
    ws_url: str,
    input_folder: str,
    output_folder: str,
    sl: str,
    tl: str,
    concurrency: int,
    delete_input: bool,
    log_callback: Callable[[str], None],
    app_state: dict,
):
    log_callback("Bắt đầu lấy danh sách ảnh từ thư mục đầu vào...")
    image_files = []

    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    for root, _, files in os.walk(input_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_exts:
                image_files.append(os.path.join(root, file))

    if not image_files:
        log_callback("Không tìm thấy ảnh hợp lệ (.png, .jpg, .jpeg, .webp, .gif) trong thư mục.")
        return

    queue = asyncio.Queue()
    for img in image_files:
        queue.put_nowait(img)

    for _ in range(concurrency):
        queue.put_nowait(None)

    log_callback(f"Đã thêm {len(image_files)} ảnh vào hàng đợi. Khởi chạy {concurrency} workers song song...")

    async with async_playwright() as p:
        try:
            log_callback("Kết nối vào Cửa sổ Chrome mặc định...")
            browser = await p.chromium.connect_over_cdp(ws_url)
            
            # Tái sử dụng chính Context (Window) mặc định mà Chrome vừa bật lên
            if not browser.contexts:
                context = await browser.new_context(locale="en-US")
            else:
                context = browser.contexts[0]
            
            log_callback("Thu dọn các Tab cũ để làm sạch không gian làm việc...")
            # Tạo 1 tab tạm để giữ cho Chrome không bị tắt hoàn toàn khi close các tab khác
            keeper_page = await context.new_page()
            
            for page in context.pages:
                if page != keeper_page:
                    try:
                        await page.close()
                    except:
                        pass
            
            tasks = []
            for i in range(concurrency):
                task = asyncio.create_task(
                    translate_worker(i + 1, queue, context, output_folder, sl, tl, log_callback, app_state)
                )
                tasks.append(task)

            # Wait for all workers to finish processing
            await asyncio.gather(*tasks)
            
            # Đóng keeper tab sau khi hoàn tất phiên dịch
            try:
                await keeper_page.close()
            except:
                pass
                
            log_callback("Đang ngắt kết nối Playwright...")
            await browser.close()
        except Exception as e:
            log_callback(f"Lỗi khởi tạo Playwright CDP trung tâm: {str(e)}")

    if delete_input:
        log_callback("Bắt đầu xoá thư mục đầu vào theo yêu cầu...")
        try:
            shutil.rmtree(input_folder, ignore_errors=True)
            log_callback("Đã dọn dẹp thư mục đầu vào.")
        except Exception as e:
            log_callback(f"Lỗi khi xoá thư mục đầu vào: {str(e)}")

    log_callback("Tiến trình tự động hoá đã hoàn thành.")
