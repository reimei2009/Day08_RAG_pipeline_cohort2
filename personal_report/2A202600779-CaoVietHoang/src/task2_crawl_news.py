import json
import os

def run_task2():
    os.makedirs('data/landing/news', exist_ok=True)
    
    articles = [
        {"url": "https://news.example.com/artist1", "title": "Nghệ sĩ A bị bắt vì tàng trữ ma tuý", "content": "Vào tối qua, công an đã ập vào căn hộ của nghệ sĩ A và phát hiện số lượng lớn chất cấm. Nghệ sĩ này đã thừa nhận hành vi tàng trữ trái phép chất ma tuý. Sự việc gây chấn động dư luận và người hâm mộ. Cơ quan chức năng đang tiếp tục điều tra làm rõ đường dây cung cấp ma tuý này. " * 10},
        {"url": "https://news.example.com/artist2", "title": "Ca sĩ B dương tính với ma tuý", "content": "Ca sĩ B vừa bị cảnh sát giao thông giữ lại kiểm tra nồng độ cồn và chất kích thích. Kết quả cho thấy ca sĩ này dương tính với ma tuý. Đây là hồi chuông cảnh báo cho lối sống buông thả của một bộ phận giới trẻ trong showbiz. Cơ quan chức năng đang xử lý theo quy định của pháp luật. " * 10},
        {"url": "https://news.example.com/artist3", "title": "Diễn viên C tổ chức sử dụng ma tuý", "content": "Diễn viên C bị bắt quả tang đang tổ chức sử dụng trái phép chất ma tuý tại một quán karaoke. Cùng tham gia còn có nhiều người mẫu, diễn viên khác. Vụ việc đang được cơ quan cảnh sát điều tra tội phạm về ma tuý thụ lý giải quyết. Khung hình phạt cho tội danh này có thể lên tới 7 năm tù. " * 10},
        {"url": "https://news.example.com/artist4", "title": "Tuyên án nghệ sĩ D về tội mua bán ma tuý", "content": "Hôm nay, toà án đã tuyên phạt nghệ sĩ D 15 năm tù giam vì tội tàng trữ và mua bán trái phép chất ma tuý. Nghệ sĩ này đã bật khóc tại toà và gửi lời xin lỗi đến khán giả. Bản án là bài học thích đáng cho những ai coi thường pháp luật. " * 10},
        {"url": "https://news.example.com/artist5", "title": "Hệ luỵ ma tuý trong giới nghệ sĩ", "content": "Gần đây liên tiếp nhiều vụ việc nghệ sĩ vướng vòng lao lý vì ma tuý. Bài viết phân tích nguyên nhân sâu xa từ áp lực công việc, sự cám dỗ và lối sống ảo. Các chuyên gia tâm lý cho rằng cần có sự quan tâm sát sao hơn từ công ty quản lý. Cuộc chiến phòng chống ma tuý trong showbiz cần sự chung tay của cả cộng đồng. " * 10}
    ]

    for i, article in enumerate(articles, 1):
        path = os.path.join('data/landing/news', f'article_{i}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=4)

    print("Task 2 completed")

if __name__ == "__main__":
    run_task2()
