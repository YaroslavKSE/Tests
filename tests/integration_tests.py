from api import app
from api_resources.UsersReportResource import UsersReportResource
from sql_db_models.setup_database import setup_db
from sql_db_models.database_populator import populate_data

import unittest
import time


class IntegrationTest(unittest.TestCase):

    def setUp(self):
        # Set up the testing client
        self.app = app.test_client()

        # Pre-populate the database with known data
        self.populate_test_data()

    def tearDown(self):
        UsersReportResource.reports = {}
        UsersReportResource.report_configs = {}

    def populate_test_data(self):
        setup_db()

        current_time = time.strftime('%Y-%m-%dT%H:%M:%S')
        user_id = "e51c2535-test-test-test-aa7af408e927"
        is_online = True
        last_seen = "2023-10-02T08:28:29.0102812+00:00"
        start_online_time = "2023-10-05T17:01:17"
        end_online_time = "2023-10-05T17:05:32"

        populate_data(current_time, user_id, is_online, last_seen, start_online_time, end_online_time)

        self.current_time = current_time
        self.user_id = user_id
        self.is_online = is_online
        self.last_seen = last_seen
        self.start_online_time = start_online_time
        self.end_online_time = end_online_time

    def test_api_response_data_exists_about_all_users_online(self):
        response = self.app.get(f'/api/stats/users?date={self.current_time}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"usersOnline": 5})

    def test_api_response_data_not_exists_about_all_users_online(self):
        # Query a date for which we haven't populated data
        wrong_time = '2077-01-01T00:00:00'
        response = self.app.get(f'/api/stats/users?date={wrong_time}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"usersOnline": None})

    def test_api_response_data_for_a_concrete_user_which_is_online_at_correct_time(self):
        response = self.app.get(f'/api/stats/users?date={self.start_online_time}&userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "wasUserOnline": True,
            "nearestOnlineTime": None
        })

    def test_api_response_data_for_a_concrete_user_which_is_online_at_incorrect_time(self):
        wrong_time = '2077-01-01T00:00:00'
        response = self.app.get(f'/api/stats/users?date={wrong_time}&userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "wasUserOnline": False,
            "nearestOnlineTime": self.end_online_time
        })

    def test_api_response_data_for_a_concrete_user_which_is_online_invalid_user_id(self):
        invalid_user_id = 'user_no_info_12312312'
        response = self.app.get(f'/api/stats/users?date={self.current_time}&userId={invalid_user_id}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {'error': 'User not found.'})

    def test_api_response_data_for_a_concrete_user_which_is_online_no_nearest_online_time_found(self):
        wrong_time = '2077-01-01T00:00:00'
        user_with_no_timespan = "e51c2535-test-test-test-no_time_span"
        response = self.app.get(f'/api/stats/users?date={wrong_time}&userId={user_with_no_timespan}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "wasUserOnline": False,
            "nearestOnlineTime": None
        })

    def test_successful_api_response_for_predicting_online_user_count(self):
        base_time_for_prediction = "2023-12-01T22:08:45"
        mean_number_of_online_users = 59
        response = self.app.get(f'/api/predictions/users?date={base_time_for_prediction}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"onlineUsers": mean_number_of_online_users})

    def test_unsuccessful_api_response_for_predicting_online_user_count(self):
        base_time_for_prediction = "2023-12-01T12:08:45"
        response = self.app.get(f'/api/predictions/users?date={base_time_for_prediction}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"onlineUsers": None})

    def test_successful_api_response_for_predicting_the_chance_of_being_user_online(self):
        response = self.app.get(f'/api/predictions/users?date={self.start_online_time}&tolerance={0.75}&'
                                f'userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "willBeOnline": True,
            "onlineChance": 1.0
        })

    def test_unsuccessful_api_response_for_predicting_the_chance_of_being_user_online(self):
        response = self.app.get(f'/api/predictions/users?date={self.current_time}&tolerance={0.75}&'
                                f'userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "willBeOnline": False,
            "onlineChance": 0
        })

    def test_successful_api_response_for_calculating_total_seconds_user_was_online(self):
        response = self.app.get(f'/api/stats/user/total?userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "totalTime": 255
        })

    def test_api_for_calculating_total_seconds_user_was_online_if_system_has_no_info_about_user(self):
        invalid_user_id = 'user_no_info_12312312'
        response = self.app.get(f'/api/stats/user/total?userId={invalid_user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "totalTime": None
        })

    def test_api_successful_response_for_calculating_daily_and_weekly_average(self):
        response = self.app.get(f'/api/stats/user/total?userId={self.user_id}&averageRequired=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "dayAverage": 255,
            "weekAverage": 255
        })

    def test_api_response_for_calculating_daily_and_weekly_average_if_the_user_not_found(self):
        user_not_fount = 'user_no_info_12312312'
        response = self.app.get(f'/api/stats/user/total?userId={user_not_fount}&averageRequired=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "dayAverage": None,
            "weekAverage": None
        })

    def test_api_response_user_data_was_forgotten(self):
        response = self.app.get(f'/api/user/forget?userId={self.user_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "userId": f"Data about {self.user_id} was forgotten"
        })

    def test_api_ForgetUserResource_user_not_found(self):
        invalid_user_id = 'user_no_info_12312312'
        response = self.app.get(f'/api/user/forget?userId={invalid_user_id}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {
            "error": "user not found"
        })

    def test_api_ForgetUserResource_no_user_id_provided(self):
        response = self.app.get(f'/api/user/forget?userId=')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {
            "error": "userId parameter is required"
        })

    def test_post_report_response_status_code_200_if_the_metrics_and_users_are_provided(self):
        # Given
        report_name = "test_report"
        payload = {
            "metrics": ["dailyAverage", "weeklyAverage", "total"],
            "users": [
                "9dcfd7a8-1a8a-e410-df25-0111bf54ba96",
                "39a28b40-dde6-84ec-c96e-dacc075effcb",
                "61b26e2c-a0d1-4461-aa80-13241ec292e1"
            ]
        }

        # When
        response = self.app.post(f'/api/report/{report_name}', json=payload)

        # Then
        self.assertEqual(response.status_code, 200)

        # Check if the report has been generated and stored.
        self.assertTrue(report_name in UsersReportResource.reports)

    def test_get_report_response_status_200_len_report_dict_is_equal_to_user_count(self):
        # Given
        report_name = "test_report"

        # We assume the report "test_report" is already generated.
        # For this test's purpose, let's manually add it.
        UsersReportResource.reports[report_name] = {
            "9dcfd7a8-1a8a-e410-df25-0111bf54ba96": {"dailyAverage": 1000, "total": 5000, "weeklyAverage": 3000},
            "39a28b40-dde6-84ec-c96e-dacc075effcb": {"dailyAverage": 1500, "total": 4500, "weeklyAverage": 3200},
            "61b26e2c-a0d1-4461-aa80-13241ec292e1": {"Error": "user not found"}
        }

        # When
        response = self.app.get(f'/api/report/{report_name}')

        # Then
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(len(data), 3)

    def test_get_all_reports_response_status_200(self):
        post_data = {
            "Name": "test_report",
            "metrics": ["dailyAverage", "weeklyAverage", "total"],
            "users": ["9dcfd7a8-1a8a-e410-df25-0111bf54ba96",
                      "39a28b40-dde6-84ec-c96e-dacc075effcb",
                      "61b26e2c-a0d1-4461-aa80-13241ec292e1"]

        }
        # post data
        response = self.app.post('/api/report/test_report', json=post_data)
        self.assertEqual(response.status_code, 200)
        # get data
        response = self.app.get('/api/reports')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # Check data
        self.assertEqual(len(data), 1)

        self.assertEqual(data[0]['Name'], 'test_report')
        self.assertEqual(data[0]['metrics'], ["dailyAverage", "weeklyAverage", "total"])
        self.assertEqual(data[0]['users'], ["9dcfd7a8-1a8a-e410-df25-0111bf54ba96",
                                            "39a28b40-dde6-84ec-c96e-dacc075effcb",
                                            "61b26e2c-a0d1-4461-aa80-13241ec292e1"])

    def test_UsersListResource_status_code_200_and_list_is_formatted(self):
        # Send a GET request to the server and receive the response
        response = self.app.get(f'/api/users/list')

        # Assert that the status code is 200
        self.assertEqual(response.status_code, 200)

        # Assert that the response content type is application/json
        self.assertEqual(response.content_type, 'application/json')

        # Load the response data
        response_data = response.get_json()

        # Assert the structure of the response
        self.assertIsInstance(response_data, list)
        for user in response_data:
            self.assertIn('userId', user)
            self.assertIn('nickname', user)
            self.assertIn('firstSeen', user)


if __name__ == '__main__':
    unittest.main()
