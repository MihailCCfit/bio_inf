#!/usr/bin/env bash
REFERENCE="$1"
FASTQ1="$2"
FASTQ2="$3"
#sudo ./script.sh ./hg38.fa.gz ./SRR12799740_1.fastq.gz ./SRR12799740_2.fastq.gz
echo $REFERENCE $FASTQ1 $FASTQ2
zcat $FASTQ1 $FASTQ2 | fastqc stdin:fastqc_results
echo "end fastqc"
echo "start indexing"
minimap2 -d ref.mmi $REFERENCE
echo "end indexing"
echo "start alignment"
minimap2 -a ref.mmi $FASTQ1 $FASTQ2 > alignment.sam
echo "end alignment"

samtools view -buT $REFERENCE alignment.sam > alg.bam
rm alignment.sa
PARSE_RES=$(python3 parseMappedResult.py "samtools_result.txt")
if [[ $PARSE_RES == "BAD" ]];
then
echo "BAD MAPPING :(";
exit 1;
fi
samtools sort "alg.bam" -o "alg.sorted.bam"
zcat $REFERENCE > "ref.fa"
freebayes "ref.fa" "alg.sorted.bam" > "sample.vcf