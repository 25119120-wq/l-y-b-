import pygame
from pygame.locals import *
import openpyxl
import random
from pygamevideo import Video

# ==================== KHỞI TẠO GAME ====================
# Khởi tạo Pygame
pygame.init()
pygame.font.init()

# ==================== CÀI ĐẶT FONT CHỮ ====================
# Font cho câu hỏi, đáp án, tiền thưởng và đồng hồ đếm ngược
font_cau_hoi = pygame.font.SysFont("Tahoma", 26, bold=True)
font_dap_an = pygame.font.SysFont("Tahoma", 24, bold=True)
font_tien_cuoi = pygame.font.SysFont("Tahoma", 55, bold=True)
font_timer = pygame.font.SysFont("Consolas", 70, bold=True)

# ==================== CÀI ĐẶT MÀN HÌNH ====================
screen_width = 1300
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Ai là triệu phú")

# ==================== TIỀN THƯỞNG THEO CẤP ĐỘ ====================
# Danh sách các mức tiền thưởng và tọa độ Y tương ứng trên thanh tiền
money_values = ["100", "200", "300", "500", "1,000", "2,000", "4,000", "8,000", 
                "16,000", "25,000", "50,000", "100,000", "250,000", "500,000", "1,000,000"]
money_y_coords = [645, 600, 565, 525, 485, 445, 405, 365, 320, 280, 240, 200, 160, 115, 70]

# ==================== LOAD HÌNH ẢNH ====================
background_playing = pygame.transform.smoothscale(pygame.image.load("playing.png"), (1300, 800))  # Nền khi chơi
background_start = pygame.image.load("background.png")  # Nền màn hình bắt đầu
background_end = pygame.transform.smoothscale(pygame.image.load("end.png"), (1300, 800))  # Nền màn hình kết thúc
button_original = pygame.image.load("start.png")   
button_start_image = pygame.transform.smoothscale(button_original, (250, 100))  # Nút bắt đầu

# ==================== LOAD ÂM THANH ====================
sound_game = pygame.mixer.Sound("lv_0_20260501135018.mp3")  # Nhạc nền
nen=pygame.mixer.Sound("nhacnen.mp3")

# ==================== LOAD VIDEO (MÀN HÌNH CHỜ) ====================
video_background = Video("1440655983638329575.mp4")
video_background.play()      # Phát video
video_background.is_looped = True   # Lặp lại vô hạn
click_sound = pygame.mixer.Sound("start.mp3")  # Âm thanh khi bấm nút

# ==================== ĐỊNH NGHĨA CÁC NÚT BẤM ====================
stop_button_rect = pygame.Rect(430, 735, 180, 50)   # Nút dừng cuộc chơi
rect_5050 = pygame.Rect(400, 690, 90, 60)           # Nút trợ giúp 50:50
rect_audience = pygame.Rect(570, 690, 90, 60)       # Nút trợ giúp khán giả
restart_button_rect = pygame.Rect(400, 550, 500, 150) # Nút chơi lại

# ==================== VÙNG ĐÁP ÁN (CÁC Ô A, B, C, D) ====================
rect_a = pygame.Rect(0, 0, 480, 80); rect_a.center = (300, 535)
rect_b = pygame.Rect(0, 0, 480, 80); rect_b.center = (800, 535)
rect_c = pygame.Rect(0, 0, 480, 80); rect_c.center = (300, 625)
rect_d = pygame.Rect(0, 0, 480, 80); rect_d.center = (800, 625)
start_button_rect = pygame.Rect(525, 500, 250, 100)  # Nút bắt đầu ở màn hình chính

# ==================== BIẾN LOGIC GAME ====================
game_state = "start"           # Trạng thái game: "start", "playing", "end"
list_cau_hoi = []              # Danh sách câu hỏi đọc từ file Excel
cau_hien_tai = 0               # Chỉ số câu hỏi hiện tại (0-14)
final_prize = "0"              # Tiền thưởng cuối cùng
current_selection = None       # Đáp án người chơi vừa chọn
is_animating = False           # Đang trong trạng thái hiệu ứng chuyển câu
anim_start_time = 0            # Thời điểm bắt đầu hiệu ứng
question_start_time = 0        # Thời điểm bắt đầu câu hỏi (để tính thời gian)
sound_game.play()              # Phát nhạc nền

# ==================== TRỢ GIÚP ====================
used_5050 = used_audience = False   # Đã sử dụng trợ giúp chưa
hidden_answers = []                 # Các đáp án bị ẩn (50:50)
purple_answers = []                 # Các đáp án được khán giả gợi ý (màu tím)

# ==================== HÀM VẼ CHỮ TỰ ĐỘNG XUỐNG DÒNG ====================
def ve_chu_da_dong(text, font, color, x, y, max_width):
    """
    Vẽ chữ lên màn hình, tự động xuống dòng nếu quá dài
    text: nội dung cần vẽ
    font: font chữ
    color: màu sắc
    x, y: tọa độ trung tâm
    max_width: chiều rộng tối đa cho phép
    """
    if text is None: return
    words = str(text).split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)
    total_height = len(lines) * font.get_linesize()
    start_y = y - total_height // 2
    for i, line in enumerate(lines):
        img = font.render(line.strip(), True, color)
        rect = img.get_rect(center=(x, start_y + i * font.get_linesize() + font.get_linesize() // 2))
        screen.blit(img, rect)

# ==================== HÀM ĐỌC DỮ LIỆU TỪ FILE EXCEL ====================
def load_data():
    """
    Đọc câu hỏi từ file Book1.xlsx
    Mỗi câu hỏi là 1 tuple: (STT, Câu hỏi, Đáp án A, B, C, D, Đáp án đúng)
    """
    questions = []
    try:
        workbook = openpyxl.load_workbook("Book1.xlsx", data_only=True)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[1]: questions.append(row)
        workbook.close()
    except: 
        return None
    return questions

# ==================== VÒNG LẶP CHÍNH CỦA GAME ====================
running = True
clock = pygame.time.Clock()
while running:
    current_ticks = pygame.time.get_ticks()  # Lấy thời gian hiện tại (ms)
    
    # ==================== XỬ LÝ SỰ KIỆN ====================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Xử lý khi click chuột và không đang trong hiệu ứng
        if event.type == pygame.MOUSEBUTTONDOWN and not is_animating:
            
            # ---------------- MÀN HÌNH BẮT ĐẦU ----------------
            if game_state == "start" and start_button_rect.collidepoint(event.pos):
                list_cau_hoi = load_data()
                if list_cau_hoi: 
                    click_sound.play()
                    game_state = "playing"
                    cau_hien_tai = 0
                    final_prize = "0"
                    used_5050 = used_audience = False
                    hidden_answers = purple_answers = []
                    question_start_time = current_ticks   # Bắt đầu đếm thời gian cho câu đầu

            # ---------------- MÀN HÌNH KẾT THÚC ----------------
            elif game_state == "end" and restart_button_rect.collidepoint(event.pos):
                click_sound.play()
                game_state = "start"   # Quay lại màn hình bắt đầu

            # ---------------- MÀN HÌNH ĐANG CHƠI ----------------
            elif game_state == "playing":
                
                # Nút trợ giúp 50:50 - Ẩn 2 đáp án sai ngẫu nhiên
                if rect_5050.collidepoint(event.pos) and not used_5050:
                    dap_an_dung = str(list_cau_hoi[cau_hien_tai][6]).strip().upper()
                    sai_list = [opt for opt in ["A", "B", "C", "D"] if opt != dap_an_dung]
                    hidden_answers = random.sample(sai_list, 2)  # Chọn ngẫu nhiên 2 đáp án sai để ẩn
                    used_5050 = True
                
                # Nút trợ giúp khán giả - Chọn 2 đáp án để highlight màu tím
                elif rect_audience.collidepoint(event.pos) and not used_audience:
                    purple_answers = random.sample(["A", "B", "C", "D"], 2)  # Gợi ý ngẫu nhiên 2 đáp án
                    used_audience = True
                
                # Nút dừng cuộc chơi - Nhận tiền thưởng hiện tại
                elif stop_button_rect.collidepoint(event.pos):
                    final_prize = money_values[cau_hien_tai - 1] if cau_hien_tai > 0 else "0"
                    game_state = "end"
                
                # Chọn đáp án
                else:
                    choice = None
                    # Kiểm tra click vào ô đáp án nào (không bị ẩn bởi 50:50)
                    if rect_a.collidepoint(event.pos) and "A" not in hidden_answers: choice = "A"
                    elif rect_b.collidepoint(event.pos) and "B" not in hidden_answers: choice = "B"
                    elif rect_c.collidepoint(event.pos) and "C" not in hidden_answers: choice = "C"
                    elif rect_d.collidepoint(event.pos) and "D" not in hidden_answers: choice = "D"

                    if choice:
                        current_selection = choice
                        is_animating = True           # Bắt đầu hiệu ứng
                        anim_start_time = current_ticks  # Ghi nhận thời điểm bắt đầu hiệu ứng

    # ==================== LOGIC CHÍNH CỦA GAME ====================
    if game_state == "playing":
        nen.play()
        # Đếm ngược thời gian (30 giây mỗi câu)
        if not is_animating:
            time_left = 30 - (current_ticks - question_start_time) // 1000
            if time_left <= 0:
                final_prize = "0"   # Hết giờ -> không được gì cả
                game_state = "end"
        
        # Xử lý kết quả sau khi hết hiệu ứng (sau 2 giây)
        if is_animating and current_ticks - anim_start_time > 2000:
            data = list_cau_hoi[cau_hien_tai]
            
            # Kiểm tra đáp án đúng hay sai
            if current_selection == str(data[6]).strip().upper():
                # ĐÚNG: Chuyển sang câu tiếp theo hoặc kết thúc
                if cau_hien_tai == 14:  # Câu cuối cùng (câu 15)
                    final_prize = money_values[14]  # 1,000,000
                    game_state = "end"
                else:
                    cau_hien_tai += 1
                    hidden_answers = purple_answers = []  # Reset trợ giúp cho câu mới
                    question_start_time = pygame.time.get_ticks()  # Reset đồng hồ
            else:
                # SAI: Kết thúc game, không có tiền
                final_prize = "0"
                game_state = "end"
            
            # Reset trạng thái hiệu ứng
            is_animating = False
            current_selection = None

    # ==================== VẼ GIAO DIỆN THEO TRẠNG THÁI ====================
    
    # ---------------- MÀN HÌNH BẮT ĐẦU ----------------
    if game_state == "start":
        video_background.draw_to(screen, (0, 0))  # Phát video nền
        screen.blit(background_start, (320, 220))      
        screen.blit(button_start_image, start_button_rect)    
    
    # ---------------- MÀN HÌNH ĐANG CHƠI ----------------
    elif game_state == "playing":
        # Vẽ nền
        screen.blit(background_playing, (0, 0))
        
        # Vẽ thanh tiền thưởng bên phải, highlight câu hiện tại
        for i in range(15):
            color = (255, 255, 255) if i != cau_hien_tai else (255, 215, 0)  # Màu vàng cho câu hiện tại
            screen.blit(font_dap_an.render(f"${money_values[i]}", True, color), (1125, money_y_coords[i] - 10))
        
        # Vẽ đồng hồ đếm ngược (chỉ hiển thị khi không có hiệu ứng)
        if not is_animating:
            ve_chu_da_dong(str(time_left), font_timer, (255, 0, 0), 150, 330, 200)

        # Vẽ câu hỏi và các đáp án
        if list_cau_hoi:
            data = list_cau_hoi[cau_hien_tai]
            
            # Vẽ câu hỏi
            ve_chu_da_dong(f"{cau_hien_tai + 1}. {data[1]}", font_cau_hoi, (255, 255, 255), 550, 100, 850)
            
            # Vẽ 4 đáp án A, B, C, D
            opts, txts, crds = ["A", "B", "C", "D"], [data[2], data[3], data[4], data[5]], [(300, 535), (800, 535), (300, 625), (800, 625)]
            for i in range(4):
                if opts[i] in hidden_answers: continue  # Bỏ qua đáp án bị ẩn (50:50)
                
                color = (255, 255, 255)  # Màu trắng mặc định
                if opts[i] in purple_answers: color = (160, 32, 240)  # Màu tím cho trợ giúp khán giả
                
                # HIỆU ỨNG KHI CHỌN ĐÁP ÁN
                if is_animating and opts[i] == current_selection:
                    dt = current_ticks - anim_start_time  # Thời gian đã trôi qua từ lúc chọn
                    if dt < 800:
                        color = (255, 215, 0)      # 0.8 giây đầu: màu vàng (chờ)
                    else:
                        # Sau 0.8 giây: xanh nếu đúng, đỏ nếu sai
                        color = (0, 255, 0) if current_selection == str(data[6]).strip().upper() else (255, 0, 0)
                
                ve_chu_da_dong(txts[i], font_dap_an, color, crds[i][0], crds[i][1], 400)

    # ---------------- MÀN HÌNH KẾT THÚC ----------------
    elif game_state == "end":
        screen.blit(background_end, (0, 0))
        # Hiển thị số tiền thưởng nhận được
        ve_chu_da_dong(f"${final_prize}", font_tien_cuoi, (255, 255, 0), 640, 230, 600)
    
    # Cập nhật màn hình và giới hạn FPS
    pygame.display.update()
    clock.tick(60)

# ==================== THOÁT GAME ====================
pygame.quit()