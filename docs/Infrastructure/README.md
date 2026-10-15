# Infrastructure – DevOps Project

## 1. Tổng quan

Hạ tầng đồ án DevOps được triển khai trên một máy Windows sử dụng Oracle VirtualBox 7.2.20.

Hệ thống gồm hai máy ảo Ubuntu Server 22.04 LTS:

- VM1: `jenkins-server` – dành cho Jenkins CI/CD và Docker.
- VM2: `k3s-server` – dành cho Kubernetes k3s và Istio.

## 2. Cấu hình máy ảo

| Thuộc tính | VM1 – Jenkins | VM2 – Kubernetes |
|---|---|---|
| Hostname | jenkins-server | k3s-server |
| OS | Ubuntu Server 22.04 LTS | Ubuntu Server 22.04 LTS |
| vCPU | 2 | 3 |
| RAM | 3 GB | 7 GB |
| Disk | 35 GB | 60 GB |
| Network 1 | NAT – DHCP | NAT – DHCP |
| Network 2 | Host-only | Host-only |
| IP Host-only | 192.168.100.10/24 | 192.168.100.20/24 |
| SSH | Port 22 | Port 22 |

## 3. Cấu hình mạng

Mạng Host-only dành riêng cho đồ án:

- Subnet: `192.168.100.0/24`
- Windows Host: `192.168.100.1`
- Jenkins Server: `192.168.100.10`
- Kubernetes Server: `192.168.100.20`
- DHCP Host-only: Disabled

Mỗi VM sử dụng NAT để truy cập Internet và Host-only để giao tiếp nội bộ.

IP tĩnh được cấu hình bằng Netplan trong file:

`/etc/netplan/60-devops-hostonly.yaml`

## 4. Kiểm tra kết nối

Các kiểm tra đã hoàn thành:

- VM1 và VM2 truy cập Internet.
- Windows SSH thành công vào VM1 và VM2.
- VM1 và VM2 ping được nhau qua Host-only.
- OpenSSH Server hoạt động trên cả hai VM.

Ví dụ SSH từ Windows:

```powershell
ssh devops@192.168.100.10
ssh devops@192.168.100.20
```

## 5. Snapshot

| VM | Snapshot | Mục đích |
|---|---|---|
| jenkins-server | VM1-Ubuntu-Base | Khôi phục Ubuntu trước khi cài Jenkins và Docker |
| k3s-server | VM2-Ubuntu-Base | Khôi phục Ubuntu trước khi cài Kubernetes và Istio |

Snapshot được tạo sau khi Ubuntu, mạng và SSH hoạt động ổn định.

Lưu ý: Snapshot không thay thế bản backup độc lập.

## 6. Trạng thái triển khai

**Đã hoàn thành:**
- GitHub repository và cấu trúc dự án.
- Cài đặt VirtualBox.
- Tạo hai VM Ubuntu Server.
- Cấu hình NAT và Host-only.
- Cấu hình IP tĩnh.
- Kiểm tra kết nối mạng và SSH.
- Tạo snapshot cho cả hai VM.

**Tiếp theo:**
- Cấu hình Tailscale để các thành viên truy cập từ xa.
- Thiết lập tài khoản và phân quyền.
- Bàn giao hạ tầng cho TV2, TV3 và TV4.

## 8. Lưu ý bảo mật

Không đưa mật khẩu, private SSH key, token hoặc thông tin xác thực nhạy cảm lên GitHub.
