from setuptools import setup
import os
from glob import glob

package_name = 'arm_camera'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],

    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name]
        ),
        (
            'share/' + package_name,
            ['package.xml']
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')
        ),
    ],

    install_requires=['setuptools'],
    zip_safe=True,

    maintainer='Dakshesh',
    maintainer_email='daksheshnankani1405@gmail.com',
    description='Camera and ArUco perception package',
    license='Apache-2.0',

    entry_points={
        'console_scripts': [
            'camera_node = arm_camera.camera_node:main',
            'aruco_detector = arm_camera.aruco_detector:main',
        ],
    },
)