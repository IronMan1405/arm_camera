'''
to run the calibration script from the package directory:
python3 arm_camera/calibrate_camera.py \
    --square-size 0.025

where 0.025 is the side length of a single square in the checkerboard in meters
i.e., if side length is 25mm then the argument is 0.025

if the board as different dimensions:
python3 src/arm_camera/arm_camera/calibrate_camera.py \
    --columns 9 \
    --rows 6 \
    --square-size 0.025 \
    --width 640 \
    --height 480

the script defaults to writing in config/camera_params.yaml

NOTE: you must run colcon build and source once calibration is done for the new parameters to be taken into effect.
'''


import argparse
from pathlib import Path

import cv2
import numpy as np
import yaml

def calibrate_camera(args):
    board_size = (args.columns, args.rows)
    square_size = args.square_size

    object_points_template = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    object_points_template[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    object_points_template *= square_size

    object_points = []
    image_points = []

    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        raise RuntimeError("Unable to open camera")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    print("\nCamera calibration started.")
    print(f"Checkerboard: {args.columns} x {args.rows} inner corners")
    print(f"Square size: {square_size} metres")
    print("\nControls:")
    print("  SPACE : Capture detected checkerboard")
    print("  Q     : Finish and calibrate")
    print("  ESC   : Exit without saving")
    print("\nMove and tilt the checkerboard between captures.\n")

    image_size = None

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("Unable to retrieve camera frame.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if image_size is None:
                image_size = gray.shape[::-1]

            found, corners = cv2.findChessboardCorners(gray, board_size, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)

            display = frame.copy()

            if found:
                refined_corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                cv2.drawChessboardCorners(display, board_size, refined_corners, found)
                status = "CHECKERBOARD DETECTED - Press SPACE"
            else:
                status = "Checkerboard not detected"

            cv2.putText(display, status, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0) if found else (0, 0, 255), 2)
            cv2.putText(display, f"Samples: {len(image_points)}", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 0), 2)
            cv2.imshow("Camera Calibration", display)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC
                print("Calibration cancelled.")
                return

            elif key == ord("q"):
                break

            elif key == 32:  # SPACE
                if found:
                    object_points.append(object_points_template.copy())
                    image_points.append(refined_corners.copy())

                    print(f"Captured sample {len(image_points)}")
                else:
                    print("No checkerboard detected. Sample skipped.")

    finally:
        camera.release()
        cv2.destroyAllWindows()

    if len(image_points) < 10:
        print(
            f"Only {len(image_points)} samples captured. "
            "At least 10 are required. Try again."
        )
        return

    print("\nCalculating camera calibration...")

    rms, camera_matrix, distortion, rvecs, tvecs = (cv2.calibrateCamera(object_points, image_points, image_size, None, None))

    rectification_matrix = np.eye(3, dtype=np.float64)

    projection_matrix = np.zeros((3, 4), dtype=np.float64)
    projection_matrix[:, :3] = camera_matrix

    calibration_data = {
        "image_width": int(image_size[0]),
        "image_height": int(image_size[1]),
        "camera_name": "camera_top",

        "camera_matrix": {
            "rows": 3,
            "cols": 3,
            "data": camera_matrix.flatten().tolist()
        },

        "distortion_model": "plumb_bob",

        "distortion_coefficients": {
            "rows": 1,
            "cols": len(distortion.flatten()),
            "data": distortion.flatten().tolist()
        },

        "rectification_matrix": {
            "rows": 3,
            "cols": 3,
            "data": rectification_matrix.flatten().tolist()
        },

        "projection_matrix": {
            "rows": 3,
            "cols": 4,
            "data": projection_matrix.flatten().tolist()
        }
    }

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as file:
        yaml.safe_dump(calibration_data, file, sort_keys=False)

    print("\nCalibration completed!")
    print(f"Reprojection RMS error: {rms:.4f} pixels")
    print("\nCamera matrix:")
    print(camera_matrix)

    print("\nDistortion coefficients:")
    print(distortion)

    print(f"\nSaved calibration to: {output_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate the overhead camera using a checkerboard.")

    parser.add_argument("--camera", type=int, default=0, help="Camera device index (default: 0)")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--columns", type=int, default=9, help="Number of inner checkerboard corners horizontally")
    parser.add_argument("--rows", type=int, default=6, help="Number of inner checkerboard corners vertically")
    parser.add_argument("--square-size", type=float, required=True, help="Actual checkerboard square side length in metres")
    parser.add_argument("--output", type=str, default="src/arm_camera/config/camera_params.yaml", help="Output calibration YAML path")
    args = parser.parse_args()

    if args.columns < 2 or args.rows < 2 or args.square_size <= 0:
        parser.error("Invalid checkerboard dimensions or square size.")

    calibrate_camera(args)

if __name__ == "__main__":
    main()
