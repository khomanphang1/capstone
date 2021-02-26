from ltspice2svg import asc_to_svg

asc_file = (r'C:\Users\shuof\PycharmProjects\capstone\test_data'
            r'\2N3904_common_emitter.asc')

with open(asc_file, 'r') as f:
    asc = f.read()
    svg = asc_to_svg(asc)
    print(svg)