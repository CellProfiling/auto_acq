<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output indent="yes"/>
	<!-- JobId / BlockId -->
	<xsl:param name="BLOCKID" select="'0'"/>
	<!-- Attributes to change -->
	<xsl:param name="NEWBLOCKID"/>
	<xsl:param name="ELEMENTID" select="'0'"/>
	<xsl:param name="BLOCKNAME" select="'0'"/>
	<xsl:param name="SEQ" select="'0'"/>
	<xsl:param name="USNAME" select="'0'"/>
	
	<xsl:template match="node()|@*">
		<xsl:copy>
			<xsl:apply-templates select="node()|@*"/>
		</xsl:copy>
	</xsl:template>
	<!-- Copy & BlockID, Element -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Element_List/LDM_Block_Sequence_Element/@BlockID">
	    <xsl:attribute name="BlockID">
			<xsl:value-of select="$BLOCKID"/>
		</xsl:attribute>
	    <xsl:choose>
			<xsl:when test="./@BlockID=$BLOCKID">
			    <xsl:attribute name="BlockID">
					<xsl:value-of select="$NEWBLOCKID"/>
				</xsl:attribute>				
			</xsl:when>
		</xsl:choose>
	</xsl:template>
	<!-- Copy & BlockID, Block -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/@BlockID">
	    <xsl:choose>
			<xsl:when test="not($BLOCKID='0') and @BlockID=$BLOCKID">
    			<xsl:copy-of select="current()"/>
			    <xsl:attribute name="BlockID">
					<xsl:value-of select="$NEWBLOCKID"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- BlockName -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/LDM_Block_Sequential/@BlockName">
	    <xsl:choose>
			<xsl:when test="$BLOCKID='0' and ../../@BlockID=$NEWBLOCKID">
		        <xsl:attribute name="BlockName">
					<xsl:value-of select="$BLOCKNAME"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
<!-- UserSettingName -->
	<!-- Master -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/LDM_Block_Sequential/LDM_Block_Sequential_Master/ATLConfocalSettingDefinition/@UserSettingName">
	    <xsl:choose>
			<xsl:when test="$BLOCKID='0' and $SEQ='0' and ../../../../@BlockID=$NEWBLOCKID">
		        <xsl:attribute name="UserSettingName">
					<xsl:value-of select="$USNAME"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- Sequence 1 -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/LDM_Block_Sequential/LDM_Block_Sequential_List/ATLConfocalSettingDefinition[1]/@UserSettingName">
	    <xsl:choose>
			<xsl:when test="$BLOCKID='0' and $SEQ='1' and ../../../../@BlockID=$NEWBLOCKID">
		        <xsl:attribute name="UserSettingName">
					<xsl:value-of select="$USNAME"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- Sequence 2 -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/LDM_Block_Sequential/LDM_Block_Sequential_List/ATLConfocalSettingDefinition[2]/@UserSettingName">
	    <xsl:choose>
			<xsl:when test="$BLOCKID='0' and $SEQ='2' and ../../../../@BlockID=$NEWBLOCKID">
		        <xsl:attribute name="UserSettingName">
					<xsl:value-of select="$USNAME"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- Sequence 3 -->
	<xsl:template match="Configuration/LDM_Block_Sequence/LDM_Block_Sequence_Block_List/LDM_Block_Sequence_Block/LDM_Block_Sequential/LDM_Block_Sequential_List/ATLConfocalSettingDefinition[3]/@UserSettingName">
	    <xsl:choose>
			<xsl:when test="$BLOCKID='0' and $SEQ='3' and ../../../../@BlockID=$NEWBLOCKID">
		        <xsl:attribute name="UserSettingName">
					<xsl:value-of select="$USNAME"/>
				</xsl:attribute>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
			        <xsl:apply-templates select="node()|@*"/>
		        </xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
</xsl:stylesheet>
