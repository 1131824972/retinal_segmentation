import requests
import json
import time


class IntegrationTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def test_health(self):
        """测试健康检查"""
        response = requests.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✅ 健康检查通过")
        return True

    def test_file_upload(self, image_path):
        """测试文件上传"""
        with open(image_path, 'rb') as f:
            files = {'file': f}
            start_time = time.time()
            response = requests.post(f"{self.base_url}/api/v1/upload/predict", files=files)
            processing_time = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        print(f"✅ 文件上传通过 - 处理时间: {processing_time:.2f}s")
        return True

    def test_all_endpoints(self):
        """测试所有端点"""
        print("🧪 开始集成测试...")

        tests = [
            ("健康检查", self.test_health),
            ("模型信息", lambda: requests.get(f"{self.base_url}/api/v1/model/info").status_code == 200),
        ]

        for test_name, test_func in tests:
            try:
                test_func()
                print(f"✅ {test_name}通过")
            except Exception as e:
                print(f"❌ {test_name}失败: {e}")
                return False

        print("🎉 所有集成测试通过！")
        return True


if __name__ == "__main__":
    tester = IntegrationTester()
    tester.test_all_endpoints()