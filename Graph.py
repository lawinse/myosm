# -*- coding:utf-8 -*-
import shapefile
import mapnik
from Config import *
from PIL import Image

class Graph:
    NodeShell = shapefile.Writer(shapefile.POINT)
    WayShell = shapefile.Writer(shapefile.POLYLINE)
    PolygonShell = shapefile.Writer(shapefile.POLYGON)
    NeighWay = shapefile.Writer(shapefile.POLYLINE)
    PathPoint = shapefile.Writer(shapefile.POINT)
    SrcPoint = shapefile.Writer(shapefile.POINT)
    neighPoint = shapefile.Writer(shapefile.POINT)

    DefaultFormat = '\t<Layer name="XXX">\n\t\t<StyleName>XXX</StyleName>\n\t\t\t<Datasource>\
                    \n\t\t\t\t<Parameter name="type">shape</Parameter>\n\
                    <Parameter name="file">XXX.shp</Parameter>\n\t\t\t</Datasource>\n\t</Layer>'
    OutputFormat = ''

    def __init__(self, file_name=WORK_DIR+"fig/style.xml"):
        f = open(file_name,'r+')
        for item in f.readlines():
            self.OutputFormat = self.OutputFormat + item

    '''x, y, and optional z (elevation) and m (measure) value.'''
    '''nodes_coord = [[coord1_x,coord1_y],[coord2_x,coord2_y]]'''
    def add_background_points(self, nodes_coord = None, nodes_id = None, nodes_add = WORK_DIR+'fig/background_points.shp'):
        if len(nodes_coord) == 0: return;
        for l1 in xrange(len(nodes_coord)):
            Graph.PathPoint.point(nodes_coord[l1][1],nodes_coord[l1][0])  # no elevation value or measure value

        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','background_points')
        Graph.PathPoint.save(nodes_add)

    '''add target nodes'''
    def add_target_points(self, nodes_coord = None, nodes_id = None, nodes_add = WORK_DIR+'fig/target_points.shp'):
        if len(nodes_coord) == 0: return;
        for l1 in xrange(len(nodes_coord)):
            Graph.PathPoint.point(nodes_coord[l1][1],nodes_coord[l1][0])  # no elevation value or measure value

        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','target_points')
        Graph.PathPoint.save(nodes_add)

    '''add root nodes'''
    def add_root_points(self, nodes_coord = None, nodes_id = None, nodes_add = WORK_DIR+'fig/root_points.shp'):
        if len(nodes_coord) == 0: return;
        for l1 in xrange(len(nodes_coord)):
            Graph.PathPoint.point(nodes_coord[l1][1],nodes_coord[l1][0])  # no elevation value or measure value

        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','root_points')
        Graph.PathPoint.save(nodes_add)

    '''add the neighbor points'''
    def add_nnode(self, nodes_coord = None, nodes_id = None, nodes_add = WORK_DIR+'fig/neigh_nodes.shp'):
        if len(nodes_coord) == 0: return;
        for l1 in xrange(len(nodes_coord)):
            Graph.PathPoint.point(nodes_coord[l1][1],nodes_coord[l1][0])  # no elevation value or measure value

        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','neigh_nodes')
        Graph.PathPoint.save(nodes_add)

    '''ways = [[[start_x,start_y],[end_x,end_y]]],[[start_x2,start2_y],[end2_x,end2_y]]], add target way'''
    def add_target_lines(self, ways = None, way_name = None, way_add = WORK_DIR+'fig/target_lines.shp'):
        if len(ways) == 0: return;
        rotate_way = []
        for item in ways:
            single_way = [[itr[1],itr[0]] for itr in item]
            rotate_way.append(single_way)
        
        self.WayShell.line(parts = rotate_way)
        self.WayShell.field('_FLD','C','40')
        self.WayShell.record('ss','Line')
        self.WayShell.save(way_add)
        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','target_lines')

    '''add another way'''
    def add_background_lines(self, ways = None, way_name = None, way_add = WORK_DIR+'fig/background_lines.shp'):
        if len(ways) == 0: return;
        rotate_way = []
        for item in ways:
            single_way = [[itr[1],itr[0]] for itr in item]
            rotate_way.append(single_way)
        
        self.WayShell.line(parts = rotate_way)
        self.WayShell.field('_FLD','C','40')
        self.WayShell.record('ss','Line')
        self.WayShell.save(way_add)
        self.OutputFormat = self.OutputFormat+'\n'+self.DefaultFormat.replace('XXX','background_lines')

    def add_area(self, area= None, area_name = None, area_add = WORK_DIR+'fig\my_area.shp'):
        if not len(area) == len(area_name):
            print 'area does not match corresponding name'
            return None
        pass

    def xml_render(self,file_name,out_size=(1280,720)):
        OutputFile = open(WORK_DIR+'fig/mystyle.xml','w')
        OutputFile.write(self.OutputFormat+'\n</Map>')
        OutputFile.close()

        stylesheet = WORK_DIR+'fig/mystyle.xml'
        image = file_name
        graph = mapnik.Map(10000, 5625)  # 16:9
        mapnik.load_map(graph, stylesheet)
        graph.zoom_all()
        mapnik.render_to_file(graph, image, 'png8:z=1:e=miniz')
        im = Image.open(image);
        rsz = im.resize(out_size,Image.ANTIALIAS);
        rsz.save(image)
        
        print "rendered image to '%s'" % image

    def render(self, shp_address=[WORK_DIR+'all_point.shp',WORK_DIR+'path_point.shp',\
        WORK_DIR+'way.shp',WORK_DIR+'src_point.shp'], \
        save_add = WORK_DIR+'output.png', graph_size = [1200,1200], bg = '#000000'):

        graph = mapnik.Map(graph_size[0],graph_size[1])

        style = mapnik.Style()
        rule = mapnik.Rule()

        #polygon_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color('white'))
        #rule.symbols.append(polygon_symbolizer)

        point_symbolizer = mapnik.PointSymbolizer(mapnik.PathExpression(WORK_DIR+"fig\red_small.png"))
        rule.symbols.append(point_symbolizer)

        apoint_symbolizer = mapnik.PointSymbolizer(mapnik.PathExpression(WORK_DIR+"fig\blue_small.png"))  #along the path
        rule.symbols.append(apoint_symbolizer)

        line_symbolizer = mapnik.LineSymbolizer(mapnik.Color('#00FA9A'),3) #the path
        rule.symbols.append(line_symbolizer)

        ypoint_symbolizer = mapnik.PointSymbolizer(mapnik.PathExpression(WORK_DIR+"fig\yellow_small.png")) # the src point
        rule.symbols.append(ypoint_symbolizer)

        style.rules.append(rule)
        graph.backgroud = mapnik.Color(bg)
        graph.append_style('default', style)
        #layer = ['polygon','line','point']
        #address = [poly_add, line_add, node_add]

        layer = ['point','point','line','point']
        address = [item for item in shp_address]

        for l1 in xrange(len(address)):
            ds = mapnik.Shapefile(file = address[l1])
            lay = mapnik.Layer(layer[l1])
            lay.datasource = ds
            lay.styles.append('default')
            graph.layers.append(lay)

        graph.zoom_all()
        mapnik.render_to_file(graph, save_add, 'png')

if __name__ == '__main__':
    My_graph = Graph()
    #My_graph.add_node([[7,3],[9,8],[11,2]],[5,6,7])
    #My_graph.add_pnode([[3,3],[5,7],[15,3]],[2,3,4])
    #My_graph.add_way([[[1,2],[3,3]],[[5,7],[15,3]]],[1,2])
    My_graph.add_snode([[1,2]],[1])
    #My_graph.xml_render()