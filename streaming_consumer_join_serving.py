import configparser
import argparse

from pyspark.context import SparkContext
from pyspark.sql import SparkSession

from pyspark.sql.functions import split, col, window, concat, lit,current_timestamp
from pyspark.sql.types import TimestampType, IntegerType,DecimalType
def foreach_batch_function(df, epoch_id, config):
    print ("Group C Batch %d received" % epoch_id)
    
    url = config['DEFAULT']['rdbms_url']
    table = config['DEFAULT']['rdbms_table']
    mode = "append"
    props = {"user":config['DEFAULT']['rdbms_user'],
             "password":config['DEFAULT']['rdbms_password'], 
             "driver":config['DEFAULT']['rdbms_driver']}   
    
    df.select("id", "commonName", "NbBikes", "NbEmptyDocks", 
              "NbDocks", "lat", "lon") \
      .write \
      .jdbc(url,table,mode,props)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("configuration_file", 
                        help="configuration file with all the information to run the job")
    args = parser.parse_args()
    
    print ("The streaming_consumer_template is about to start...")
    
    # Read the configuration file to setup the Spark Streaming Application (job)
    #
    print ("   - Reading the configuration of my Spark Streaming Application.")
    config = configparser.ConfigParser()
    config.read(args.configuration_file)
    
    # Create a SparkSession to run our Spark Streaming Application (job)
    #
    print ("   - Creating the Spark Session that will allow me to interact with Spark.")
    sc = SparkSession.builder\
        .master('local')\
        .appName('groupassignment')\
        .getOrCreate()

    # Logic of our Spark Streaming Application (job)
    #

    # 0. Get the configurations for out use case
    kafka_input_topic = config['DEFAULT']['kafka_input_topic']
    kafka_group_id = config['DEFAULT']['kafka_group_id']
    
    # 1. Build the DataFrame from the source
    
    print ("   - Building the rawEventsDF DataFrame with data coming from Kafka.")
    rawEventsDF = sc.readStream.format("kafka") \
                                  .option("kafka.bootstrap.servers", "localhost:9092") \
                                  .option("subscribe", kafka_input_topic) \
                                  .option("startingOffsets", "latest") \
                                  .option("kafka.group.id", kafka_group_id) \
                                  .load() \
                                  .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
                                   
        
        
    #sparkDF=sc.createDataFrame(rawEventsDF) 
    #.createDataFrame(df,schema=mySchema) -->>> shema is the key 

    print ("   - Polishing raw events and building a DataFrame ready to apply the logic.")
    geoEventsDF = rawEventsDF.select(split("value",'\|').alias("fields")) \
                             .withColumn("id",col("fields").getItem(0)) \
                             .withColumn("commonName",col("fields").getItem(1)) \
                             .withColumn("NbBikes",col("fields").getItem(2).cast(IntegerType())) \
                             .withColumn("NbEmptyDocks",col("fields").getItem(3).cast(IntegerType())) \
                             .withColumn("NbDocks",col("fields").getItem(4).cast(IntegerType())) \
                             .withColumn("lat",col("fields").getItem(5).cast(DecimalType(8,6))) \
                             .withColumn("lon",col("fields").getItem(6).cast(DecimalType(6,5) )) \
                             .withColumn("proc_timestamp", current_timestamp()) \
                             .select("id", "commonName", "NbBikes", "NbEmptyDocks","NbDocks", "lat", "lon")
                             #.witWatermark("proc_timestamp","30 seconds")
                             #.dropDuplicates("guid", "proc_timestamp")

  
    # 3. Configure the sink to send the results of the processing and start the streaming query
    print ("   - Configuring the foreach sink to handle batches by ourselves.")
    streamingQuery = geoEventsDF.writeStream \
                                             .foreachBatch(lambda df,epochId:foreach_batch_function(df, epochId, config))\
                                             .start()
    # 4. Await for the termination of the Streaming Query (otherwise the SparkSession will be closed)
    print ("The streaming query is running in the background (Ctrl+C to stop it)")
    streamingQuery.awaitTermination()