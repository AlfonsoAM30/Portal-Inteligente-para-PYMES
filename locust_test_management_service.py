from locust import HttpUser, task, between


class ManagementUser(HttpUser):

    wait_time = between(1, 3)

    def on_start(self):

        # LOGIN AUTOMÁTICO
        response = self.client.post(
            "/api/management/auth/login",
            json={
                "email": "danielortega@gmail.com",
                "password": "123"
            }
        )

        if response.status_code == 200:
            data = response.json()

            self.token = data["access_token"]

            self.headers = {
                "Authorization": f"Bearer {self.token}"
            }

    @task(2)
    def get_company(self):

        self.client.get(
            "/api/management/company/1",
            headers=self.headers
        )

    @task(2)
    def get_employees(self):

        self.client.get(
            "/api/management/employees/1",
            headers=self.headers
        )

    @task(2)
    def get_profile(self):

        self.client.get(
            "/api/management/profile/1",
            headers=self.headers
        )

    @task(2)
    def get_breaches(self):
        self.client.get(
            "/api/management/breaches/1",
            headers=self.headers
        )

