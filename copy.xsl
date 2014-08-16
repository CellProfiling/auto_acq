<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output indent="yes"/>
	<!-- JobId / BlockId -->
	<xsl:param name="BLOCKID"/>
	<xsl:param name="NEWBLOCKID"/>
	<!-- Attributes to change -->
	

	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block">
	    <xsl:choose>
			<xsl:when test="../../../../../../@BlockID=$BLOCKID">
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
		        <xsl:attribute name="BlockID">
					<xsl:value-of select="$NEWBLOCKID"/>
				</xsl:attribute>
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	
	
</xsl:stylesheet>
