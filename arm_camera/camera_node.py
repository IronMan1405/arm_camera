import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image

from cv_bridge import CvBridge

import cv2, time

class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_node")

        self.top_img_raw = self.create_publisher(Image, "/camera/top/image_raw", 10)

        self.bridge = CvBridge()

        self.video = cv2.VideoCapture(0)

        if not self.video.isOpened():
            self.get_logger().error("Unable to open camera")
            raise RuntimeError("Camera initialization failed")

        self.timer = self.create_timer(1.0 / 30.0, self.get_camera_feed)

        self.get_logger().info("Camera node initialized")

    def get_camera_feed(self):
        check, frame = self.video.read()

        if not check:
            self.get_logger().warning("Frame not available")
            return

        ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        ros_image.header.stamp = self.get_clock().now().to_msg()
        ros_image.header.frame_id = "camera_top_optical_frame"

        self.top_img_raw.publish(ros_image)

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