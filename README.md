# devops-project
DevOps CI/CD Project using Jenkins, Docker, Kubernetes and Istio
# DevOps Project – Nhóm 4 thành viên

## 1. Giới thiệu

Đồ án xây dựng hệ thống DevOps sử dụng GitHub, Jenkins, Docker, Kubernetes (k3s) và Istio.

**Mục tiêu giữa kỳ:**
- UC1: Continuous Integration với Jenkins.
- UC2: Continuous Deployment lên Kubernetes.
- UC3: Publish Service thông qua Istio Gateway, DNS và HTTPS.

**Mục tiêu sau giữa kỳ:**
- UC4: Monitoring và Alerting.
- UC5: Canary Deployment và tự động Rollback.
- UC6: DevSecOps.

## 2. Phân công công việc

| Thành viên | Vai trò | Công việc |
|---|---|---|
| TV1 | Infrastructure & Integration | GitHub, VirtualBox, Ubuntu Server, mạng, SSH, Tailscale, tích hợp |
| TV2 | CI Engineer | Ứng dụng, Docker, Jenkins CI |
| TV3 | CD Engineer | Kubernetes k3s, manifests, Jenkins CD |
| TV4 | Networking & Service Engineer | Istio Gateway, DNS, HTTPS |

## 3. Cấu trúc repository

- `app/`: Mã nguồn ứng dụng.
- `tests/`: Unit test.
- `k8s/`: Kubernetes manifests.
- `istio/`: Cấu hình Istio.
- `scripts/`: Script hỗ trợ.
- `docs/infrastructure/`: Tài liệu hạ tầng.
- `docs/uc1-ci/`: Tài liệu UC1.
- `docs/uc2-cd/`: Tài liệu UC2.
- `docs/uc3-istio/`: Tài liệu UC3.
- `docs/troubleshooting/`: Nhật ký lỗi và cách khắc phục.

Các file `.gitkeep` chỉ dùng để giữ cấu trúc thư mục khi chưa có nội dung.

## 4. Quy tắc làm việc

1. Sử dụng một GitHub repository chung.
2. Mỗi thành viên phát triển trên branch riêng, không trực tiếp sửa `main`.
3. Tạo Pull Request và review trước khi merge.
4. Không đưa token, mật khẩu hoặc private key lên GitHub.
5. Thử nghiệm Kubernetes trong namespace riêng.
6. Chỉ triển khai lên namespace `devops-demo` khi đã kiểm tra.
7. Ghi nhật ký cài đặt, lỗi và cách khắc phục.
8. Snapshot VM sau mỗi mốc ổn định.

## 5. Hạ tầng dự kiến

Hệ thống sử dụng một máy Windows chạy VirtualBox với hai VM:

- VM1: Ubuntu Server, Jenkins và Docker.
- VM2: Ubuntu Server, Kubernetes k3s và Istio.

Các thành viên truy cập từ xa thông qua Tailscale sau khi hạ tầng được cấu hình.


