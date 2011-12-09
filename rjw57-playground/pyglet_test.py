from math import sqrt, sin, cos, pi
import numpy as np
import cv2
import ctypes

from pyglet.gl import *
import pyglet

from shader import Shader
from tracker_app import TrackerApp
import threading

def rotate(angle, axis):
  """Return a rotation matrix which rotates by angle radians around the axis axis."""
  s = sin(angle)
  c = cos(angle)
  x,y,z = axis
  return np.matrix(np.array((
    (x*x*(1-c) +   c, y*x*(1-c) - z*s, z*x*(1-c) + y*s),
    (x*y*(1-c) + z*s, y*y*(1-c) +   c, z*y*(1-c) - x*s),
    (x*z*(1-c) - y*s, y*z*(1-c) + x*s, z*z*(1-c) +   c),
    )))

class ShaderGroup(pyglet.graphics.Group):
  def __init__(self, shader, *args, **kwargs):
    super(ShaderGroup, self).__init__(*args, **kwargs)
    self.shader = shader

  def set_state(self):
    self.shader.bind()

  def unset_state(self):
    self.shader.unbind()

  def __eq__(self, other):
    return self.__class__ is other.__class__ and self.shader == other.shader

class RenderableObject(object):
  def __init__(self, batch = None):
    # Create a batch if necessary
    if batch is None:
      batch = pyglet.graphics.Batch()
    self.batch = batch

  def draw(self):
    self.batch.draw()

class SetPoseGroup(pyglet.graphics.Group):
  """Given a shader, set the uniform 4x4 matrix 'pose' in the shader to a homogenous pose matrix."""

  def __init__(self, shader, *args, **kwargs):
    super(SetPoseGroup, self).__init__(*args, **kwargs)
    self.shader = shader
    self.pose_matrix = np.matrix(np.identity(4))

  def set_state(self):
    self.shader.uniform_matrixf('pose', np.array(self.pose_matrix).flatten('F').tolist())

  def set_pose(self, pose):
    self.pose_matrix = np.matrix(np.array(pose))

  def set_axes(self, x=(1,0,0), y=(0,1,0), z=(0,0,1)):
    self.pose_matrix[0:3,0] = np.matrix(np.array(x)).transpose()
    self.pose_matrix[0:3,1] = np.matrix(np.array(y)).transpose()
    self.pose_matrix[0:3,2] = np.matrix(np.array(z)).transpose()

  def set_ypr(self, yaw=0, pitch=0, roll=0):
    # Calculate rotation matrix
    R = rotate(yaw, (0,1,0))
    roll_axis = R * np.matrix((1,0,0)).transpose()
    R = rotate(roll, roll_axis) * R
    pitch_axis = R * np.matrix((0,0,1)).transpose()
    R = rotate(pitch, pitch_axis) * R
    self.pose_matrix[0:3,0:3] = R

  def set_origin(self, origin=(0,0,0)):
    t = np.matrix(np.array(origin)).transpose()
    self.pose_matrix[0:3,3] = t

class QuadRotor(RenderableObject):

  def __init__(self, batch = None, group = None, size=0.5):
    super(QuadRotor, self).__init__(batch)

    self.shader = Shader(
    vert = ['''
    uniform mat4 pose;

    void main() {
      gl_Position = gl_ModelViewProjectionMatrix * pose * gl_Vertex;
      vec3 normal = (pose * vec4(gl_Normal, 0.)).xyz;
      float diffuse = dot(normal, vec3(1,1,1)/sqrt(3.));

      // port left, starboard green
      vec3 colour = (gl_Vertex.z < 0.) ? vec3(1,0,0) : vec3(0,1,0);

      // front blue
      colour.z = (gl_Vertex.x > 0.) ? 1. : 0.;

      gl_FrontColor.rgb = clamp(diffuse, 0., 1.) * colour;
    }
    '''],
    frag = ['''
    void main() {
      gl_FragColor = gl_Color;
    }
      '''])

    self.group = SetPoseGroup(self.shader, ShaderGroup(self.shader, group))

    # Generate rotors - the origin is roughly the centre of gravity with the
    # +xve xaxis being the camera axis
    thickness = 0.012
    height = 0.025
    self._add_rotor(-0.5*size, -0.25*size, 0.25*size + 0.5*thickness, thickness=thickness, height=height)
    self._add_rotor(-0.5*size,  0.25*size, 0.25*size + 0.5*thickness, thickness=thickness, height=height)
    self._add_rotor( 0. *size,  0.25*size, 0.25*size + 0.5*thickness, thickness=thickness, height=height)
    self._add_rotor( 0. *size, -0.25*size, 0.25*size + 0.5*thickness, thickness=thickness, height=height)

    # Add an arrow
    self._add_arrow(origin=(0,0,0), size=size, majoraxis=(1,0,0), minoraxis=(0,0,1))

    self.set_pose()

  def set_pose(self, origin=(0,0,0), yaw=0, pitch=0, roll=0):
    self.group.set_origin(origin)
    self.group.set_ypr(yaw, pitch, roll)

  def set_pose_matrix(self, m):
    self.group.set_pose(m)

  def _add_arrow(self, origin, size, majoraxis, minoraxis):
    # FIXME: Implement
    pass

  def _add_rotor(self, xc, zc, outer_radius, thickness=0.05, height=0.05, subdivcount=32):
    vertices = []
    normals = []
    indices = []

    # Calculate rotor vertex vertices
    for point_idx in range(subdivcount):
      angle = point_idx * 2.0 * pi / subdivcount
      s = sin(angle)
      c = cos(angle)

      # Outer circle
      xo = xc + outer_radius * s
      zo = zc + outer_radius * c

      # Inner circle
      xi = xc + (outer_radius - thickness) * s
      zi = zc + (outer_radius - thickness) * c

      vs = []
      vs.extend((xo,  0.5*height, zo))
      vs.extend((xo, -0.5*height, zo))
      vs.extend((xi,  0.5*height, zi))
      vs.extend((xi, -0.5*height, zi))

      # Outer and inner circle vertices
      vertices.extend(vs)
      normals.extend((s,0,c, s,0,c, -s,0,-c, -s,0,-c))

      # Top and bottom vertices
      vertices.extend(vs)
      normals.extend((0,1,0, 0,-1,0, 0,1,0, 0,-1,0))

    # Outer curve
    indices.append((subdivcount-1) * 8 + 1)
    indices.append((subdivcount-1) * 8 + 1)
    indices.append((subdivcount-1) * 8)
    for idx in range(subdivcount):
      indices.extend((idx*8 + 1, idx*8))
    indices.append(indices[-1])

    # Inner curve
    indices.append((subdivcount-1) * 8 + 2)
    indices.append((subdivcount-1) * 8 + 2)
    indices.append((subdivcount-1) * 8 + 3)
    for idx in range(subdivcount):
      indices.extend((idx*8 + 2, idx*8 + 3))
    indices.append(indices[-1])

    # Bottom
    indices.append((subdivcount-1) * 8 + 7)
    indices.append((subdivcount-1) * 8 + 7)
    indices.append((subdivcount-1) * 8 + 5)
    for idx in range(subdivcount):
      indices.extend((idx*8 + 7, idx*8 + 5))
    indices.append(indices[-1])

    # Top
    indices.append((subdivcount-1) * 8 + 4)
    indices.append((subdivcount-1) * 8 + 4)
    indices.append((subdivcount-1) * 8 + 6)
    for idx in range(subdivcount):
      indices.extend((idx*8 + 4, idx*8 + 6))
    indices.append(indices[-1])

    self.batch.add_indexed(len(vertices) / 3, GL_TRIANGLE_STRIP, self.group,
        indices, ('v3f', vertices), ('n3f', normals))

class Plane(RenderableObject):
  class ShaderGroup(ShaderGroup):
    def __init__(self, *args, **kwargs):
      super(Plane.ShaderGroup, self).__init__(*args, **kwargs)
      self.tex_region = (0,0,0,0)
      self.tex_extents = (0,0,0,0)

    def set_state(self):
      super(Plane.ShaderGroup, self).set_state()
      self.shader.uniformf('texRegion', *self.tex_region)
      self.shader.uniformf('texExtents', *self.tex_extents)

  def __init__(self, batch = None, group = None, xsize=10, zsize=2):
    super(Plane, self).__init__(batch)

    self.shader = Shader(
    vert = ['''
    uniform mat4 pose;
    void main() {
      // transform the vertex position
      gl_Position = gl_ModelViewProjectionMatrix * pose * gl_Vertex;
      // pass through the texture coordinate
      gl_TexCoord[0] = gl_MultiTexCoord0;
    }
    '''],
    frag = ['''
    uniform sampler2D tex;
    uniform vec4 texRegion; // region of plane with texture vec4(minx,maxx,minz,maxz)
    uniform vec4 texExtents; // region within texture to draw vec4(minx,maxx,miny,maxy)
    void main() {
      // make a chessboard pattern where each cell is 1/4 metre wide
      vec2 f = floor(mod(8.f * gl_TexCoord[0].xy, 2));
      float check = 0.5f + 0.25f * mod(dot(f, vec2(1,1)), 2);
      gl_FragColor = vec4(check,check,check,1);
      if((gl_TexCoord[0].x > texRegion.x) && (gl_TexCoord[0].x < texRegion.y) &&
         (gl_TexCoord[0].y > texRegion.z) && (gl_TexCoord[0].y < texRegion.w))
      {
        vec2 texCoord = (gl_TexCoord[0].xy - texRegion.xz) / (texRegion.yw - texRegion.xz);
        texCoord = (texCoord * (texExtents.yw - texExtents.xz)) + (texExtents.xz);
        gl_FragColor = texture(tex, texCoord);
      }
    }
      '''])
    self.group = group
    self.shadergroup = Plane.ShaderGroup(self.shader, self.group)
    self.posegroup = SetPoseGroup(self.shader, self.shadergroup)
    self.plane = self.batch.add(
        4, GL_QUADS, self.posegroup,
        ('v3f', (-0.5*xsize,0,-0.5*zsize, -0.5*xsize,0,0.5*zsize, 0.5*xsize,0,0.5*zsize, 0.5*xsize,0,-0.5*zsize)),
        ('t2f', (-0.5*xsize,-0.5*zsize, -0.5*xsize,0.5*zsize, 0.5*xsize,0.5*zsize, 0.5*xsize,-0.5*zsize))
    )

    self.xsize = xsize
    self.zsize = zsize
    self.set_pose((0,0,0), (1,0,0), (0,0,1))

  def migrate(self, batch=None, group=None):
    if batch is None:
      batch=self.batch
    if group is None:
      group=self.group

    self.group = group
    
    old_pose = self.posegroup.pose_matrix
    self.posegroup = SetPoseGroup(self.shader, self.shadergroup)
    self.posegroup.pose_matrix = old_pose

    self.batch.migrate(self.plane, GL_QUADS, self.posegroup, batch)
    self.batch = batch

  def pose(self):
    return self.posegroup.pose_matrix

  def set_pose(self, origin, xaxis, zaxis):
    x=np.array(xaxis)
    x/=np.linalg.norm(x)
    z=np.array(zaxis)
    z/=np.linalg.norm(z)
    y=np.cross(z,x)
    self.posegroup.set_axes(x,y,z)
    self.posegroup.set_origin(origin)

class Scene(pyglet.graphics.Group):
  def __init__(self, app, *args, **kwargs):
    super(Scene, self).__init__(*args, **kwargs)
    self.app = app
    self.batch = pyglet.graphics.Batch()

    self.floor = Plane(batch=self.batch, group=self, xsize=20, zsize=20)
    self.floor.set_pose(origin=(0,-1,0), xaxis=(1,0,0), zaxis=(0,0,1))

    self.board = Plane(batch=self.batch, group=self, xsize=20, zsize=20)
    self.board.set_pose(origin=(1,0,0), xaxis=(0,0,-1), zaxis=(0,1,0))

    self.drone = QuadRotor(batch=self.batch, group=self)
    self.drone.set_pose(origin=(0,-1,0))

    self.texture_bin = pyglet.image.atlas.TextureBin(1024,1024)
    self.board_image = None

    im = self.app.cam_image()
    im_data = pyglet.image.ImageData(im.shape[1], im.shape[0], 'RGB', str(im.data))
    self.camera_image = self.texture_bin.add(im_data)

    self.rx = 20
    self.ry = 80
    self.rz = 0
    self.t = 0
    pyglet.clock.schedule(self.update)
  
  def draw(self):
    self.batch.draw()

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    v = (ctypes.c_float * 4)()
    glGetFloatv(GL_VIEWPORT, v)
    gluOrtho2D(v[0],v[0]+v[2],v[1]+v[3],v[1])

    glColor3f(1,1,1)
    self.camera_image.blit(0,0)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

  def update(self, dt):
    im = self.app.cam_image()
    im_data = pyglet.image.ImageData(im.shape[1], im.shape[0], 'RGB', str(im.data))
    self.camera_image.blit_into(im_data, 0, 0, 0)

    try:
      board = self.app.boards()[0]
    except IndexError:
      board = None

    if board is not None:
      config, ids, recon_image, recon_mask, detect = board
      if detect[0] is not None and detect[1] > 0.1:
        # Get camera extrinsics
        rvec, tvec = [np.array(x) for x in detect[0].get_extrinsics()]

        # Convert Rodrigues vector to rotation matrix
        R = np.identity(3)
        cv2.Rodrigues(rvec, R)

        # Generate camera matrix (world -> camera)
        C = np.matrix(np.identity(4))
        C[0:3,0:3] = R
        C[0:3,3] = np.matrix(np.array(tvec)).transpose()

        # Generate camera -> world pose matrix
        M = np.linalg.inv(C)

        # Drone pose
        D = np.matrix(np.identity(4))
        D[0:3,0:3] *= rotate(-0.5*pi, (0,1,0))
        D[0:3,0:3] *= rotate(pi, (1,0,0))

        self.drone.set_pose_matrix(self.board.pose() * M * D)

        board_image = np.array(recon_image / np.maximum(recon_mask, 1), dtype=np.uint8)
        data = str(board_image.data)
        im = pyglet.image.ImageData(board_image.shape[1], board_image.shape[0], 'RGB', data)
        if self.board_image is None or \
            (self.board_image.height, self.board_image.width) != board_image.shape[0:2]:
          self.board_image = self.texture_bin.add(im)
          self.board.migrate(group=pyglet.graphics.TextureGroup(self.board_image, self))
        else:
          self.board_image.blit_into(im, 0, 0, 0)

        recon_pixel_size = 0.004 # metres (from tracker.py)
        self.board.shadergroup.tex_region = [recon_pixel_size * x for x in (
            -0.5*board_image.shape[1],  0.5*board_image.shape[1],
            -0.5*board_image.shape[0],  0.5*board_image.shape[0],
        )]
        self.board.shadergroup.tex_extents = [self.board_image.tex_coords[x] for x in (0, 6, 1, 7)]

    self.t += dt
    #self.ry += dt * 30
    #self.ry %= 360

    #self.drone.set_pose(origin=(0,-0.5,0), yaw=0, pitch=0.2*sin(self.t), roll=0.2*cos(0.5*self.t))

  def set_state(self):
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0, -0.25, -2)
    glRotatef(self.rx, 1, 0, 0)
    glRotatef(self.ry, 0, 1, 0)

    glEnable(GL_DEPTH_TEST)
    #glEnable(GL_CULL_FACE)
    glColor3f(1, 0, 0)
    
    glDisable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)

class MainWindow(pyglet.window.Window):
  def __init__(self, app, *args, **kwargs):
    super(MainWindow, self).__init__(*args, **kwargs)
    self.scene = Scene(app)

  def on_resize(self, width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60., width / float(height), .1, 100.)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED

  def on_draw(self):
    self.clear()
    self.scene.draw()

class PygletThread(threading.Thread):
  def __init__(self, app):
    super(PygletThread, self).__init__()
    self.app = app

  def run(self):
    window = MainWindow(self.app, width=1280, height=720, caption='Drone mapping test')
    pyglet.app.run()
    self.app.quit()

app = TrackerApp()

pyglet_thread = PygletThread(app)
pyglet_thread.start()

app.run()
