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
---
## 安装文件  

1. 准备核心软件  
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
---
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
python main.py --config config.toml --all # 运行全流程
# 或者独立运行某个模块
python main.py --config config.toml --cactus-pangenome # 运行构建
python main.py --config config.toml --vg # 运行统计与索引
python main.py --config config.toml --annotation # 运行注释
python main.py --config config.toml --wgs # 运行WGS比对
```  

> [!note]  
>由于其中可能存在使用singularity运行的软件, 倘若使用常用的后台方式会导致singularity终止运行, 推荐使用`tmux`创建虚拟终端进行运行.  
>```bash  
>tmux new -s graphPangenomePipeline 'python main.py --config config.toml -all'  
>```  
>此时可以通过`tmux ls`观察是否有终端在运行.  
>运行结束后, 可以通过`tmux attach -t graphPangenomePipeline`进入终端进行查看.   
---
## config文件参数配置说明  

**[Global]**  
该项下主要包含全局的参数设置  
`work_dir`  
为设置生成的pipeline文件存放的目录, 应为一个路径.  
`filePrefix`   
为cactus生成的文件名(--outName)的前缀, 应为str.

> [!note]  
> **如果是自己生成的gfa或gbz文件,  请将文件名改为`{filePrefix}.full.gfa`类似这种格式的gfa或gbz文件**

**[Cactus]**  
该项包含cactus-pangenome的部分主要设置  
`seqFile`  
为cactus-pangenome中要求的[seqFile](#配置管道-)  
`reference`  
要求和seqFile中的某个Genome序列一致, 为cactus-pangenome中要求的参考基因组(核心基因)  
`mzxCores`  
为cactus-pangenome中被允许使用的最大核心数  
`singularityImage`(可选)  
singularity容器的路径, 如果不存在可以留空为`singualrityImage = ""`或删除, 如果有指定路径, 会使用容器运行exec  

**[CactusOutFormat]**  
该项主要是修改cactus-pangenome生成的文件类型, 在cactus-pangenome中, 以下的输出参数默认写带full参数, 具体参数说明参考`cactus-pangenome help`  
`vcf` 当`true`时生成*.full.vcf  
`gfa` 当`true`时生成*.full.gfa  
`gbz` 当`true`时生成*.full.gbz

**[VgStats]**  
以下包含Vg的启用的统计类型, 包含stats和paths两块.  
当忽略运行cactus进行独立运行vg时, 输入的要求为符合filePrefix一致的文件前缀, 存放在work_dir的输出目录中, 创建一个1.cactus并存放在其中.  
`stats` 当`true`时, 运行vg stats进行pangenome的总体估计  
`paths` 当`true`时, 运行vg paths进行pangenome的路径统计(输出为p-line, 格式为: GenomeName#HalNum#ChrName)  

**[VgIndex]**  
以下为运行Vg构建索引, 以进行后续比对的设置.  
`autoindex` 当`true`时, 运行`vg autoindex`进行索引构建  
`threads` 为autoindex索引构建时使用的核心数, 输入类型为int  

**[Annotation]**  
为注释相关的的软件和文件设置, 当前仅支持**grannot**进行注释.    
`gff3` 需要提供你的reference(核心基因组)的gff3文件, 输入为gff3文件的路径    
`SourceGenome` 实际为你进行图泛构建时的使用的核心基因组, 可以等同reference的值, 输入类型为str  
`singularityImage`(可选)   
singularity容器的路径, 如果不存在可以留空为`singualrityImage = ""`或删除, 如果有指定路径, 会使用容器运行exec  

**[Gaf]**  
该参数激活时, 使用grannot注释生成图形注释文件  
`Gaf` 当`true`时, 运行grannot进行注释输出一个图像注释文件  

**[ann]**  
该参数激活时, 会使用grannot 使用annotation将reference的gff去比较到其他target基因组并生成相关统计结果  
同时, 因为在annotation下grannot给与了一些个性化的设置, 可以参考grannot的帮助文档. 在该配置字典下, 可以接收不定数量的参数,  对于输入的参数要求使用**在grannot中的参数全称(--arg)**  

以下列出的为一些默认的配置参数:  
`annotation` 为annotation的参数`--annotation`, 当该项为`true`时, 才启用ann注释  
`pav_matrix` 当该项为`true`时, 为输出Pav矩阵文件, 以观察基因之间的差异, 实际为grannot的参数 `--pav_matrix`  
`target` 实际为grannot的参数`--target`, 输入的参数为str, 如不输入, 默认值为"", 则在grannot中默认会比较所有参与构建的基因组, **请注意, 该项不确定当你输入多个参数, 使得target本身成为列表时, 会生效, 因此如果需要比较多个特定参与构建的基因组时, 该项建议留空**  

**[wgs]**  
该项为使用 `vg giraffe` 进行全基因组重测序 (WGS) 数据比对以及使用 `vg pack` 进行覆盖度统计的设置.  
`DataTable`  
输入为一个 CSV 文件的路径, 该文件描述了待比对的样本信息.  
CSV 文件要求包含以下表头:  
- `SampleID`: 样本名称.  
- `R1`: Read 1 Fastq 文件路径.  
- `R2`: Read 2 Fastq 文件路径 (可选).  
`Parallel_job`  
设置并行处理的样本数量, 输入类型为 int.  
`Threads`  
设置每个样本在运行 `vg giraffe` 和 `vg pack` 时使用的线程数, 输入类型为 int.  
`MinMapQ`  
设置 `vg pack` 时的最小比对质量 (Minimum Mapping Quality), 输入类型为 int.  

