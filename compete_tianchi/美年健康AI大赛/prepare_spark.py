import pyspark
import pyspark.sql.functions

spark=pyspark.sql.SparkSession.builder.getOrCreate()

data1=spark.read.text('file:///home/zhao/Documents/learn_python/compete_tianchi/美年健康AI大赛/data/meinian_round1_data_part1_20180408.txt')
data2=spark.read.text('file:///home/zhao/Documents/learn_python/compete_tianchi/美年健康AI大赛/data/meinian_round1_data_part2_20180408.txt')
test=spark.read.csv('file:///home/zhao/Documents/learn_python/compete_tianchi/美年健康AI大赛/data/meinian_round1_test_a_20180409.csv', encoding='GBK')
train=spark.read.csv('file:///home/zhao/Documents/learn_python/compete_tianchi/美年健康AI大赛/data/meinian_round1_train_20180408.csv', encoding='GBK')

data1.show(truncate=False)
print(data1.dtypes)
print(data1.columns)
print(data1.count())
data1.printSchema()
data1.selectExpr('value as haha').show()
data1.withColumnRenamed('value','hehe').show()
data1.select(data1.value.alias('hoho')).show()
data1.select('value').show()
data1.select(data1.value).show()
data1.select(data1[0]).show()
data1.select(data1['value']).show()
data1.select(data1['value']>=4).show()
data1.select('value').select(data1['value']>4).show()
data1.filter(data1.value.between(4,5)).select(data1.value.alias('hihi')).show()
data1.filter(data1.value>4).filter(data1[0]!='htre').show()
data1.filter("value='asdf'").show()
data1.filter("value like 'b%'").show()
data1.where("value like '%yellow%'").show()
data1.createOrReplaceTempView('data1_df')
spark.sql("select count(5) from data1_df").show()
data1.drop('value').show()
data1.withColumn('huhu',pyspark.sql.functions.lit(0)).show()
print(data1.toJSON().first())
data1.sort('value',ascending=False).show()
data1.filter(data1['value']>=4).sort('value').show()
data1.sort(data1.value.asc()).show()
data1.orderBy('value').take(4)
data1.dropna().show()
data1.na.drop().show()
data1.dropDuplicates().show()