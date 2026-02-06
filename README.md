# Graph Pangenome Pipeline  
GraphPangenomePipeline 是一个基于python的模块化的图泛基因组分析流程. 集成了目前主要使用的图泛基因组构建工具与分析工具管道.  
目前支持使用cactus-pangenome进行物种内的图泛基因组分析构建.
旨在完成从fasta序列到注释图谱以及进行重测序数据和RNA-seq数据分析的全过程.  

同时该pipeline也支持使用cactus与grannot的singularity容器运行以降低安装需求.  

该项目使用uv进行管理.  

---
## 主要特性 

 - 模块化设计: 流程解耦为独立的模块(包含构建, 索引, 注释等.), 可以独立运行某一个模块, 也可以一体化运行.  
 - 核心工具:  
   - cactus: 基于cactus-pangenome进行的物种内的图泛基因组构建.  
   - grannot: 基于grannot进行图泛基因组的注释
   - vg: 使用vg工具套件进行图谱统计和索引构建, 以及进行测序数据的比对.  
 - 容器化: cactus和grannot支持使用singularity进行运行(需要指定容器镜像文件路径)  
 - 基于toml配置文件驱动, 同时支持根据实际情况灵活调整传参.  

## 环境依赖  
 - python >= 3.13

## 安装文件  

1.准备核心软件  
关于该pipeline软件的安装可以使用以下命令进行:  
- vg  
```bash
# 使用预编译的vg软件包(v1.70.0)
wget https://github.com/vgteam/vg/releases/download/v1.70.0/vg
chmod +x vg
mv vg ~/bin/
```  
- cactus  
```bash
# 推荐使用singularity安装cactus
singularity pull cactus.sif docker://quay.io/comparative-genomics-toolkit/cactus:lastest
```  
- grannot  
```bash
# 同样推荐使用grannot官方推荐的镜像安装方式进行安装
wget https://forge.ird.fr/diade/dynadiv/grannot/-/raw/ca2fa671e3a4dbe50294abfecf77f36ac19980da/Grannot.def?inline=false
singularity build grannot.sif Grannot.def
```  
2.克隆本仓库  
```bash
git clone https://github.com/Georicl/GraphPangenomePipeline
```  
3.创建虚拟环境与安装部分依赖(倘若你使用uv)  
```bash
cd GraphPangenomePipeline
uv sync
```  

## 配置管道  
1.准备seqFile  
- seqFile: 为cactus-pangenome需要的序列配置文件  
要求为第一列为基因组名字, 第二列为序列文件的路径
```text
genomeA /path/to/genomeA.fasta
genomeB /path/to/genomeB.fasta
genomeC /path/to/genomeC.fasta
```  
2.进行文件配置  
拷贝一份`config/config.toml`到你的工作目录下, 并进行个性化的修改配置  

3.运行管道  
```bash
python main.py --config config.toml -all # 运行全流程
```  

:::note  
由于其中可能存在使用singularity运行的软件, 倘若使用常用的后台方式会导致singularity终止运行, 推荐使用`tmux`创建虚拟终端进行运行.
```bash
tmux new -s graphPangenomePipeline 'python main.py --config config.toml -all'
```  
此时可以通过`tmux ls`观察是否有终端在运行.  
运行结束后, 可以通过`tmux attach -t graphPangenomePipeline`进入终端进行查看.
:::  

### config.toml文件参数配置说明  


