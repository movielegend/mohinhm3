M3 MINI GO (trước đây: HA109) — Revision 9 / tái dựng theo ảnh

Mở xem-mo-hinh-ha109.html trong trình duyệt hỗ trợ WebGL để xoay mô hình.
GLB dùng cho Blender, Three.js hoặc các trình xem glTF.
Ảnh front, hero, rear, side được kết xuất trực tiếp từ hình học 3D.

Đã sửa: bo góc thân theo mặt bằng; dải vát đáy riêng; nắp bo viền;
tay đỡ nghiêng có đầu tròn và chân nối cong; đế mỏng bo góc;
tỷ lệ chiều sâu, vị trí lưới thoát nhiệt và tâm ống kính.
Revision 3: dựng lại khung cổng sau bo góc mảnh, HDMI có vai vát,
audio, USB và các ký hiệu; lưới 10 hàng chia đoạn dài/ngắn xen kẽ.
rear-detail.png là ảnh cận xuất trực tiếp từ mô hình.
Revision 4: mặt trên có hai dải cong lớn nhạt màu, viền nắp mảnh,
nút nguồn lõm với vành bo tròn và biểu tượng nguồn hở. top.png là góc từ trên.
Revision 5: viền ống kính tím bạc bo tròn, lòng đen nhiều lớp, kính lồi
với màu phản xạ tím/xanh mô phỏng bằng vertex color; mảng mặt trước bo dài,
cảm biến và bánh lấy nét có gân. front-detail.png là ảnh cận mặt trước.
Màu phản xạ được tạo theo ảnh, không phải mô phỏng quang học vật lý.
Revision 6: ổ nguồn số 8 có khoang sâu và hai chân tiếp xúc; 10 khe bên;
bánh lấy nét có mặt nền và gân ôm qua góc thân. left-detail.png và
left-side.png cho phép đối chiếu bên có nguồn. Lưới lỗ và đầu tay đỡ được giữ.
Revision 7: dựng lại tay đỡ với đầu tròn, nắp trục chìm, thân nghiêng,
hai đường cong chân loe và bo mép theo chiều dày. stand-detail.png là ảnh cận.
Revision 8: tăng nhẹ sắc tím lavender của thân, nắp, chân đế và hoa văn nắp.
Revision 9: tăng thêm một mức nhẹ sắc tím lavender theo yêu cầu.

Giới hạn: bán kính và kích thước suy ra từ ảnh. Quang học, hoa văn nắp,
cổng kết nối và vật liệu vẫn là mô phỏng, chưa trùng khít sản phẩm.
Không phải CAD sản xuất. Đã kiểm tra xuất/nạp GLB và render bốn góc;
chưa kiểm thử trang HTML trong trình duyệt tại môi trường dựng.

Mã nguồn kèm theo dùng Python, numpy, trimesh, manifold3d; render dùng
moderngl và Pillow. Đường dẫn /workspace trong script cần đổi nếu chạy máy khác.
