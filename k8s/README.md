Triển khai Flask trên Kubernetes k3s
Tài liệu hướng dẫn phần việc của TV3 trong dự án DevOps: triển khai ứng dụng Flask lên k3s, kiểm tra Service, scale, self-healing, rolling update và phối hợp TV1 kiểm thử Jenkins CD.
Ứng dụng Flask và Jenkins CI do TV2 phụ trách. TV1 quản lý Jenkins CD và k8s/Jenkinsfile. TV4 phụ trách Istio Gateway và VirtualService.
1. Thông tin triển khai
Thành phần	Giá trị
Repository	https://github.com/namle1602/devops-project

Máy triển khai	VM2
Tailscale IP VM2	100.101.165.112
Tài khoản SSH	tv3
Kubeconfig trên VM2	/home/tv3/.kube/config
Namespace	devops-project
Deployment	flask-deployment
Container	flask-app
Service	flask-service
Label Pod và selector Service	app: flask-app
Image ban đầu	ghcr.io/namle1602/devops-flask-app:latest
Image dùng cho CD	ghcr.io/namle1602/devops-flask-app:<CI_BUILD_TAG>
Replicas mặc định	2
Container port	5000/TCP
Service type	ClusterIP
Service port / targetPort	80 / 5000
Health endpoint	GET /health
Health response	HTTP 200, JSON {"status":"healthy"}
GHCR package được nhóm xác nhận là Public; manifest không cần imagePullSecrets. Quyền truy cập repository GitHub được quản lý riêng với quyền tải image GHCR.
2. Các file trong thư mục k8s
File	Nội dung	Phụ trách
deployment.yaml	Image, replicas, Pod template, probes và chiến lược cập nhật	TV3
service.yaml	Service ClusterIP cổng 80 trỏ đến cổng 5000	TV3
README.md	Hướng dẫn triển khai, kiểm thử và bàn giao	TV3
Jenkinsfile	Pipeline CD hiện có	TV1
Đặt tài liệu này tại k8s/README.md. TV3 giữ nguyên k8s/Jenkinsfile do TV1 quản lý.
Các lệnh có đường dẫn k8s/... bên dưới được chạy tại thư mục gốc repository.
3. Điều kiện chuẩn bị
•	Máy cá nhân kết nối Tailscale của nhóm và truy cập được VM2.
•	VM2 đã cài k3s, có kubectl và namespace devops-project.
•	Tài khoản Kubernetes có quyền đọc, tạo và chỉnh sửa Deployment/Service; đọc và xóa Pod; theo dõi rollout.
•	Quyền scale gồm quyền trên deployments/scale; port-forward cần quyền trên pods/portforward.
•	Quyền đọc log cần quyền trên pods/log. Các thao tác đọc Events, ReplicaSet hoặc EndpointSlice phụ thuộc RBAC được cấp.
•	Đã clone repository của nhóm và được cấp quyền đóng góp theo quy trình GitHub của nhóm.
•	VM2 truy cập được GHCR; cluster có đủ tài nguyên cho replicas và Pod tăng thêm khi rolling update.
Khi gặp lỗi SSH, kubeconfig, RBAC hoặc Jenkins credentials, chuyển thông báo lỗi cho TV1 xử lý.
4. Kết nối và kiểm tra cluster
Chạy trên máy cá nhân:
ssh tv3@100.101.165.112
Sau khi vào VM2:
export KUBECONFIG=/home/tv3/.kube/config
kubectl config current-context
kubectl get deployments,pods,svc -n devops-project
Mỗi phiên SSH mới cần đặt lại biến KUBECONFIG nếu môi trường chưa cấu hình sẵn. Thực hiện thao tác Kubernetes bằng tài khoản đã được cấp, không cần sudo.
Kiểm tra các quyền bổ sung dùng trong bài:
kubectl auth can-i get deployments.apps --subresource=scale -n devops-project
kubectl auth can-i update deployments.apps --subresource=scale -n devops-project
kubectl auth can-i create pods --subresource=portforward -n devops-project
kubectl auth can-i get pods --subresource=portforward -n devops-project
Nếu có kết quả no, nhờ TV1 bổ sung quyền tương ứng trước khi thực hiện thao tác đó.
5. Triển khai Deployment và Service
Đối chiếu manifest trước khi áp dụng:
•	Cả hai file có metadata.namespace: devops-project.
•	Deployment có tên flask-deployment, container có tên flask-app.
•	spec.selector.matchLabels khớp spec.template.metadata.labels.
•	Selector Service khớp label Pod app: flask-app.
•	Container chạy cổng 5000; Service ClusterIP dùng port: 80, targetPort: 5000.
•	Replicas ban đầu bằng 2.
•	Readiness và liveness probe gọi HTTP /health tại cổng 5000.
•	Chiến lược RollingUpdate dùng maxSurge: 1, maxUnavailable: 0 theo manifest hướng dẫn.
Nếu Deployment đã tồn tại với selector khác, trao đổi với TV1 trước khi áp dụng vì selector Deployment không thể chỉnh trực tiếp.
Kiểm tra manifest phía API server mà chưa ghi thay đổi:
kubectl apply --dry-run=server -f k8s/deployment.yaml -f k8s/service.yaml
Triển khai:
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
kubectl get deployments,pods,svc -n devops-project
kubectl get pods -n devops-project -l app=flask-app -o wide
Tiêu chí đạt:
•	Deployment có READY 2/2, UP-TO-DATE 2, AVAILABLE 2.
•	Hai Pod Running, tất cả container trong mỗi Pod đều Ready.
•	Service flask-service có loại ClusterIP, cổng 80/TCP.
Khi chưa có Istio sidecar, mỗi Pod thường hiển thị READY 1/1. Nếu có sidecar, tổng số container có thể lớn hơn.
6. Kiểm tra ứng dụng và health endpoint
6.1. Port-forward
Tại terminal SSH thứ nhất trên VM2:
kubectl port-forward -n devops-project service/flask-service 8080:80
Giữ terminal này hoạt động. Tại terminal SSH thứ hai trên VM2:
curl -i --max-time 10 http://127.0.0.1:8080/
curl -i --max-time 10 http://127.0.0.1:8080/health
Tiêu chí đạt: / trả HTTP 200; /health trả HTTP 200 và JSON có "status":"healthy".
Port-forward đến Service chọn một Pod phù hợp để chuyển tiếp. Phép thử này kiểm tra ứng dụng qua cổng đích của Service, không chứng minh cân bằng tải giữa tất cả Pod hoặc toàn bộ đường mạng ClusterIP.
Nếu cổng 8080 đã được sử dụng, đổi thành 8081:80 và dùng URL cổng 8081. Nếu Pod được chọn bị xóa hoặc thay thế trong lúc thử self-healing/rolling update, chạy lại port-forward.
6.2. Kiểm tra trực tiếp ClusterIP từ VM2
SERVICE_IP=$(kubectl get service flask-service -n devops-project -o jsonpath='{.spec.clusterIP}')
curl -i --max-time 10 "http://${SERVICE_IP}/health"
Tiêu chí đạt: Service chuyển tiếp được yêu cầu và /health trả HTTP 200. Nếu port-forward thành công nhưng ClusterIP thất bại, kiểm tra selector, readiness, mạng cluster và chính sách mạng với TV1.
6.3. Truy cập từ trình duyệt máy cá nhân
Trong khi port-forward trên VM2 vẫn chạy, mở terminal trên máy cá nhân:
ssh -N -L 18080:127.0.0.1:8080 tv3@100.101.165.112
Truy cập:
•	http://127.0.0.1:18080/
•	http://127.0.0.1:18080/health
Service ClusterIP không tự mở cổng 80 trên Tailscale IP của VM2.
7. Kiểm thử scale từ 2 lên 3 replicas
Phối hợp TV1 để tránh pipeline CD thay đổi Deployment trong lúc kiểm thử thủ công.
Ghi nhận trạng thái trước khi scale:
kubectl get deployment flask-deployment -n devops-project
kubectl get pods -n devops-project -l app=flask-app
Tăng lên 3 replicas:
kubectl scale deployment/flask-deployment -n devops-project --replicas=3
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
kubectl get deployment flask-deployment -n devops-project
kubectl get pods -n devops-project -l app=flask-app -o wide
Tiêu chí đạt: Deployment có READY 3/3, ba Pod Running và Ready. Kiểm tra lại /health, lưu ảnh hoặc log trước và sau scale.
Đưa về cấu hình mặc định sau kiểm thử:
kubectl scale deployment/flask-deployment -n devops-project --replicas=2
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
Lệnh scale thay đổi trạng thái trên cluster; file manifest vẫn khai báo replicas: 2.
8. Kiểm thử self-healing
Ghi nhận tên và UID Pod trước khi xóa:
kubectl get pods -n devops-project -l app=flask-app -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,PHASE:.status.phase'
Mở terminal khác để theo dõi:
kubectl get pods -n devops-project -l app=flask-app -w
Tại terminal thao tác, lấy một Pod và kiểm tra tên trước khi xóa:
POD_TO_DELETE=$(kubectl get pods -n devops-project -l app=flask-app -o jsonpath='{.items[0].metadata.name}')
echo "$POD_TO_DELETE"
Sau khi xác nhận đúng Pod Flask:
kubectl delete pod "$POD_TO_DELETE" -n devops-project
Quan sát Pod mới xuất hiện. Sau khi ổn định, nhấn Ctrl+C tại terminal theo dõi rồi kiểm tra:
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
kubectl get deployment flask-deployment -n devops-project
kubectl get pods -n devops-project -l app=flask-app -o custom-columns='NAME:.metadata.name,UID:.metadata.uid,PHASE:.status.phase'
Tiêu chí đạt:
•	Pod cũ đã được xóa.
•	ReplicaSet do Deployment quản lý tự tạo Pod thay thế có tên và UID mới.
•	Deployment trở lại đủ 2 replicas khả dụng.
•	/health thành công sau khi ổn định; chạy lại port-forward nếu cần.
9. Kiểm thử rolling update
9.1. Chọn phiên bản
Sử dụng tag theo số build Jenkins CI đã được push thành công lên GHCR và thống nhất với TV1. Không tự suy đoán tag mới hoặc dùng số build Jenkins CD thay cho tag CI.
Đổi tag trong Pod template sẽ kích hoạt rollout. Tuy nhiên, hai tag có thể trỏ đến cùng nội dung image; để chứng minh thay đổi phiên bản ứng dụng, cần hai image khác nhau và bằng chứng phiên bản hoặc digest tương ứng.
Ghi nhận image và revision trước cập nhật:
kubectl get deployment flask-deployment -n devops-project -o jsonpath='{.spec.template.spec.containers[?(@.name=="flask-app")].image}{"\n"}'
kubectl rollout history deployment/flask-deployment -n devops-project
9.2. Cập nhật image
Mở terminal theo dõi Pod:
kubectl get pods -n devops-project -l app=flask-app -w
Tại terminal thao tác, nhập tag build thực tế đã được xác nhận:
read -r -p "Nhap image tag da duoc TV1 xac nhan: " IMAGE_TAG
echo "$IMAGE_TAG"
Sau khi kiểm tra tag không rỗng và đúng phiên bản:
kubectl set image deployment/flask-deployment -n devops-project flask-app="ghcr.io/namle1602/devops-flask-app:${IMAGE_TAG}"
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
Kiểm tra image và image ID của container Flask:
kubectl get pods -n devops-project -l app=flask-app -o custom-columns='NAME:.metadata.name,IMAGE:.spec.containers[?(@.name=="flask-app")].image,IMAGE_ID:.status.containerStatuses[?(@.name=="flask-app")].imageID'
kubectl get deployment flask-deployment -n devops-project
kubectl rollout history deployment/flask-deployment -n devops-project
Chạy lại port-forward nếu phiên cũ kết thúc, sau đó kiểm tra /health.
Tiêu chí đạt: rollout hoàn thành; các Pod mới sử dụng đúng image; số replicas khả dụng trở lại 2; health endpoint trả HTTP 200.
Để đánh giá tính liên tục của dịch vụ trong thời gian rollout, theo dõi HTTP qua ClusterIP hoặc đường truy cập ổn định của nhóm. Không dùng riêng một phiên port-forward để kết luận không gián đoạn, vì phiên đó gắn với một Pod cụ thể.
9.3. Rollback khi cần
kubectl rollout undo deployment/flask-deployment -n devops-project
kubectl rollout status deployment/flask-deployment -n devops-project --timeout=180s
Kiểm tra lại image, trạng thái Deployment và /health sau rollback. Rollback là thao tác khôi phục khi cần, không phải bước bắt buộc sau mỗi lần cập nhật thành công.
9.4. Đồng bộ với manifest
kubectl set image và kubectl rollout undo không sửa file trong Git. Sau thử nghiệm, ghi nhận image cuối cùng và thống nhất với TV1 cách đồng bộ manifest/pipeline.
Việc push lại tag latest rồi apply manifest không đổi không tự kích hoạt rollout. imagePullPolicy: Always chỉ kiểm tra image khi container khởi chạy; không tự thay thế các Pod đang hoạt động.
10. Phối hợp Jenkins CD với TV1
TV1 giữ quyền quản lý k8s/Jenkinsfile. CD Build #1 được mô tả trong tài liệu phân công là bước xác nhận kết nối/quyền; để nghiệm thu triển khai phải kiểm tra đầy đủ luồng bên dưới.
1.	Jenkins CI kiểm thử, build và push image lên GHCR với tag theo số build CI.
2.	Jenkins CD nhận đúng tag CI làm tham số triển khai.
3.	CD checkout repository chứa hai manifest của TV3.
4.	CD áp dụng manifest và cập nhật container flask-app của Deployment flask-deployment sang image đã chọn.
5.	CD chờ kubectl rollout status thành công.
6.	Kiểm tra image thực tế trong Pod và HTTP /health.
Thông tin tích hợp:
Trường	Giá trị
Namespace	devops-project
Deployment	flask-deployment
Container cập nhật	flask-app
Image repository	ghcr.io/namle1602/devops-flask-app
Image tag	Tag do Jenkins CI cung cấp
Manifest	k8s/deployment.yaml, k8s/service.yaml
Health endpoint	/health
Nếu manifest vẫn chứa latest, pipeline cần quản lý thứ tự áp dụng và đổi tag để không ghi đè tag build về latest sau khi cập nhật. Có thể áp dụng manifest trước rồi đổi image, hoặc render manifest với đúng tag trước khi áp dụng theo thiết kế của TV1.
Jenkins dùng credentials do TV1 cấu hình; không commit kubeconfig, private key, Kubernetes token hoặc Jenkins credentials vào repository.
11. Thông tin bàn giao cho TV4
Trường	Giá trị
Namespace	devops-project
Service	flask-service
Service DNS	flask-service.devops-project.svc.cluster.local
Service port	80
Target port của Pod	5000
Protocol	HTTP
Health path	/health
Service đích cho cấu hình Istio:
flask-service.devops-project.svc.cluster.local:80
TV4 cấu hình đích đến Service ở cổng 80. TV3 bàn giao Service và kết quả kiểm thử, không chỉnh Gateway/VirtualService trong phạm vi này.
12. Kết quả kiểm thử
Bảng dưới đây là mẫu bàn giao được điền theo giả định tất cả kiểm thử đã PASS. Tag build, revision, tên Pod, thời điểm chạy và ảnh/log thực tế được lấy từ lần nghiệm thu của nhóm; tài liệu không tự đặt các giá trị đó.
STT	Hạng mục	Tiêu chí nghiệm thu	Kết quả
1	Xác thực manifest	Hai manifest hợp lệ khi server dry-run	PASS
2	Triển khai	Deployment đủ 2 replicas khả dụng	PASS
3	Pod	Các Pod Running và tất cả container Ready	PASS
4	Service	ClusterIP cổng 80 trỏ đến Flask cổng 5000	PASS
5	Trang chủ	GET / trả HTTP 200	PASS
6	Health endpoint	GET /health trả HTTP 200 và trạng thái healthy	PASS
7	ClusterIP	Truy cập được health qua ClusterIP từ VM2	PASS
8	Scale	Tăng 2 lên 3 replicas, đủ 3 Pod Ready	PASS
9	Khôi phục replicas	Đưa Deployment về 2 replicas sau thử scale	PASS
10	Self-healing	Pod bị xóa được thay thế, Deployment đủ replicas	PASS
11	Rolling update	Cập nhật đúng tag, rollout hoàn thành, health thành công	PASS
12	Jenkins CD	Nhận tag CI, triển khai đúng image và kiểm tra health thành công	PASS
Rollback chỉ cần ghi nhận riêng nếu thực tế đã chạy thử. Bảng này không suy ra kết quả kiểm thử Istio của TV4.
13. Bằng chứng và bàn giao GitHub
Bộ bằng chứng cần lưu:
•	Kết quả kubectl get deployments,pods,svc -n devops-project.
•	Kết quả HTTP của / và /health.
•	Trạng thái Deployment/Pod trước và sau scale.
•	Tên và UID Pod trước khi xóa, Pod thay thế sau self-healing.
•	Image/tag/digest trước và sau cập nhật, lịch sử revision, kết quả rollout.
•	Console Output hoặc kết quả Jenkins CD cùng tag CI được triển khai.
•	Commit chứa manifest và README trên main theo quy trình nhóm.
Ví dụ lưu một phần log trên VM2, khi port-forward đang hoạt động:
mkdir -p ~/tv3-evidence
kubectl get deployments,pods,svc -n devops-project | tee ~/tv3-evidence/overview.txt
kubectl rollout history deployment/flask-deployment -n devops-project | tee ~/tv3-evidence/rollout-history.txt
curl -i --max-time 10 http://127.0.0.1:8080/health 2>&1 | tee ~/tv3-evidence/health.txt
Ghi bằng chứng scale, self-healing và rollout ngay khi thực hiện để giữ được cả trạng thái trước và sau.
Kiểm tra thay đổi trước khi commit:
git status
git diff --check
git diff -- k8s/deployment.yaml k8s/service.yaml k8s/README.md
git add k8s/deployment.yaml k8s/service.yaml k8s/README.md
git diff --cached
git commit -m "Add Flask Kubernetes manifests and deployment guide"
Đưa thay đổi vào main qua pull request hoặc push trực tiếp theo quy trình nhóm. Không ghi đè Jenkinsfile và không force-push để xử lý xung đột.
14. Xử lý sự cố
Hiện tượng	Hướng kiểm tra
SSH timeout	Tailscale, trạng thái VM2, kết nối đến VM2; báo TV1
Kubernetes Forbidden	Xem thao tác, tài nguyên/subresource và namespace; nhờ TV1 bổ sung RBAC
GitHub 403	Kiểm tra quyền repository, lời mời collaborator và phương thức xác thực Git
ErrImagePull / ImagePullBackOff	Tên image, tag tồn tại, trạng thái public và mạng đến GHCR
CrashLoopBackOff	Log ứng dụng, exit code, probe và cấu hình khởi động
Pod Running nhưng chưa Ready	/health, cổng 5000 và readiness probe
Service không hoạt động	Selector, label Pod, readiness và targetPort
Pod Pending	Events, tài nguyên và ràng buộc lập lịch
Rollout timeout	Deployment/Pod Events, image pull, probe, tài nguyên cho Pod bổ sung
Port-forward bị ngắt	Chạy lại sau khi Pod được thay thế
Thay TEN_POD_THUC_TE bằng tên Pod cần kiểm tra:
kubectl describe deployment flask-deployment -n devops-project
kubectl describe pod TEN_POD_THUC_TE -n devops-project
kubectl logs TEN_POD_THUC_TE -n devops-project -c flask-app --tail=100
kubectl logs TEN_POD_THUC_TE -n devops-project -c flask-app --previous --tail=100
kubectl describe service flask-service -n devops-project
kubectl get pods -n devops-project -l app=flask-app --show-labels
kubectl get events -n devops-project --sort-by=.metadata.creationTimestamp
Lệnh logs --previous chỉ áp dụng khi có lần chạy container trước đó. Một số lệnh chẩn đoán cần thêm quyền đọc tương ứng.

