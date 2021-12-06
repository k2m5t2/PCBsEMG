import cv2
import keyboard
import numpy as np
import open3d as o3d
import pygame
from transforms3d.axangles import axangle2mat

import sys
sys.path.insert(0, './visualizer')

from hand_mesh import HandMesh
from kinematics import mpii_to_mano
from utils import OneEuroFilter, imresize
# from wrappers import ModelPipeline
from utils import *

CAM_FX = 620.744
CAM_FY = 621.151
HAND_COLOR = [228/255, 178/255, 148/255]


def live_application():
  """
  Launch an application that reads from a webcam and estimates hand pose at
  real-time.
  The captured hand must be the right hand, but will be flipped internally
  and rendered.
  Parameters
  ----------
  capture : object
    An object from `capture.py` to read capture stream from.
  """
  ############ output visualization ############
  view_mat = axangle2mat([1, 0, 0], np.pi) # align different coordinate systems
  window_size = 1079

  hand_mesh = HandMesh("./visualizer/hand_mesh_model.pkl")
  mesh = o3d.geometry.TriangleMesh()
  mesh.triangles = o3d.utility.Vector3iVector(hand_mesh.faces)
  mesh.vertices = \
    o3d.utility.Vector3dVector(np.matmul(view_mat, hand_mesh.verts.T).T * 1000)
  mesh.compute_vertex_normals()

  viewer = o3d.visualization.Visualizer()
  viewer.create_window(
    width=window_size + 1, height=window_size + 1,
    window_name='Minimal Hand - output'
  )
  viewer.add_geometry(mesh)

  view_control = viewer.get_view_control()
  cam_params = view_control.convert_to_pinhole_camera_parameters()
  extrinsic = cam_params.extrinsic.copy()
  extrinsic[0:3, 3] = 0
  cam_params.extrinsic = extrinsic
  cam_params.intrinsic.set_intrinsics(
    window_size + 1, window_size + 1, CAM_FX, CAM_FY,
    window_size // 2, window_size // 2
  )
  view_control.convert_from_pinhole_camera_parameters(cam_params)
  view_control.set_constant_z_far(1000)

  render_option = viewer.get_render_option()
  render_option.load_from_json('./render_option.json')
  viewer.update_renderer()

  ############ input visualization ############
  # pygame.init()
  # display = pygame.display.set_mode((window_size, window_size))
  # pygame.display.set_caption('Minimal Hand - input')

  ############ misc ############
  mesh_smoother = OneEuroFilter(4.0, 0.0)
  clock = pygame.time.Clock()

  while True:
    theta_mpii = [[0] * 4] * 21
    theta_mano = mpii_to_mano(theta_mpii)
    # theta_mano = [0] * 60

    v = hand_mesh.set_abs_quat(theta_mano)
    v *= 2 # for better visualization
    v = v * 1000 + np.array([0, 0, 400])
    v = mesh_smoother.process(v)
    mesh.triangles = o3d.utility.Vector3iVector(hand_mesh.faces)
    mesh.vertices = o3d.utility.Vector3dVector(np.matmul(view_mat, v.T).T)
    mesh.paint_uniform_color(HAND_COLOR)
    mesh.compute_triangle_normals()
    mesh.compute_vertex_normals()
    viewer.update_geometry(mesh)

    viewer.poll_events()

    # display.blit(
    #   pygame.surfarray.make_surface(
    #     np.transpose(
    #       imresize(frame_large, (window_size, window_size)
    #     ), (1, 0, 2))
    #   ),
    #   (0, 0)
    # )
    # pygame.display.update()

    if keyboard.is_pressed("esc"):
      break

    clock.tick(80)


if __name__ == '__main__':
  live_application()