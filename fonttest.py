import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 替代 Noto Sans SC
rcParams['axes.unicode_minus'] = False  # 让负号正常显示


plt.title("头道拐-万家寨")
plt.plot([1, 2, 3], [4, 5, 6], label="测试线")
plt.legend()
plt.xlabel("横轴：时间")
plt.ylabel("纵轴：流量")
plt.savefig("test_output.png", dpi=150)
plt.show()
