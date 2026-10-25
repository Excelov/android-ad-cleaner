import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "skill" / "android-ad-optimizer" / "scripts" / "android_ad_optimizer.py"
SPEC = importlib.util.spec_from_file_location("android_ad_optimizer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ChannelParsingTests(unittest.TestCase):
    def test_candidates_keep_orders_and_skip_ambiguous_channels(self):
        dump = """
    PackagePreferences:
      AppSettings: com.example.shop
        NotificationChannel{mId='promo', mName=内容与营销, mDescription=, mImportance=3, mDeleted=false}
        NotificationChannel{mId='order', mName=订单通知, mDescription=, mImportance=3, mDeleted=false}
        NotificationChannel{mId='other', mName=其他, mDescription=, mImportance=3, mDeleted=false}
"""
        channels = MODULE.parse_channels(dump)
        by_id = {row["id"]: row for row in channels}
        self.assertTrue(by_id["promo"]["candidate"])
        self.assertFalse(by_id["order"]["candidate"])
        self.assertFalse(by_id["other"]["candidate"])

    def test_deleted_and_off_channels_are_not_candidates(self):
        dump = """
    PackagePreferences:
      AppSettings: com.example.app
        NotificationChannel{mId='off', mName=活动优惠, mDescription=, mImportance=0, mDeleted=false}
        NotificationChannel{mId='deleted', mName=活动优惠, mDescription=, mImportance=3, mDeleted=true}
"""
        self.assertEqual(MODULE.candidates({"channels": MODULE.parse_channels(dump)}), [])


if __name__ == "__main__":
    unittest.main()
