import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CameraInfo
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge

import cv2, os, yaml

class CameraNode(Node):
	def __init__(self):
		super().__init__("camera_node")

		self.top_img_raw = self.create_publisher(Image, "/camera/top/image_raw", 10)
		self.camera_info_pub = self.creat_publisher(CameraInfo, "/camera/top/camera_info", 10)

		self.bridge = CvBridge()

		### NOTE: current camera_params.yaml does not have calibrated values, make sure to change it before using it
		package_share = get_package_share_directory("arm_camera")

		calibration_file = os.path.join(package_share, "config", "camera_params.yaml")

		with open(calibration_file, "r") as file:
			self.calibration = yaml.safe_load(file)

		self.video = cv2.VideoCapture(0)

		if not self.video.isOpened():
			self.get_logger().error("Unable to open camera")
			raise RuntimeError("Camera initialization failed")

		self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
		self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

		self.camera_info_msg = self.create_camera_info()

		self.timer = self.create_timer(1.0 / 30.0, self.get_camera_feed)

		self.get_logger().info("Camera node initialized")

	def create_camera_info(self):
		calibration = self.calibration

		msg = CameraInfo()
		msg.width = calibration["image_width"]
		msg.height = calibration["image_height"]
		msg.distortion_model = calibration["distortion_model"]
		msg.d = calibration["distortion_coefficients"]["data"]
		msg.k = calibration["camera_matrix"]["data"]
		msg.r = calibration["rectification_matrix"]["data"]
		msg.p = calibration["projection_matrix"]["data"]

		return msg

	def get_camera_feed(self):
		check, frame = self.video.read()
		if not check:
			self.get_logger().warning("Frame not available")
			return

		height, width = frame.shape[:2]

		if (width != self.camera_info_msg.width or
				height != self.camera_info_msg.height):
			self.get_logger().error(
				"Captured resolution does not match calibration resolution"
			)
			return

		timestamp = self.get_clock().now().to_msg()

		ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
		ros_image.header.stamp = timestamp
		ros_image.header.frame_id = "camera_top_optical_frame"

		self.camera_info_msg.header.stamp = timestamp
		self.camera_info_msg.header.frame_id = "camera_top_optical_frame"

		self.top_img_raw.publish(ros_image)
		self.camera_info_pub.publish(self.camera_info_msg)

	def destroy_node(self):
		if hasattr(self, "video") and self.video.isOpened():
			self.video.release()

		super().destroy_node()

def main(args=None):
	rclpy.init(args=args)
	node = CameraNode()

	try:
		rclpy.spin(node)
	except KeyboardInterrupt:
		pass
	finally:
		rclpy.destroy_node()
		rclpy.shutdown()

if __name__ == "__main__":
	main()