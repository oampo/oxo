#! /usr/bin/env python
import os.path
import re
import argparse
import distutils.dir_util

import pystache
from pygments import highlight
from pygments.lexers import JavascriptLexer
from pygments.formatters import HtmlFormatter
import markdown2

class OXO:
    def __init__(self):
        # Input files
        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--title", default="Documentation")
        parser.add_argument("-d", "--description", default="")
        parser.add_argument("-s", "--section-title", action="append")
        parser.add_argument("-i", "--infile", nargs="+", required=True,
                            action="append", type=argparse.FileType('r'))
        parser.add_argument("-o", "--outfile", required=True,
                            type=argparse.FileType('w'))

        args = parser.parse_args()

        sections = []
        files = []
        if args.section_title:
            if len(args.section_title) != len(args.infile):
                parser.print_help()
                exit(0)
            sections = []
            for title, infiles in zip(args.section_title, args.infile):
                sections.append(Section(title, infiles))
        else:
            for jsFile in args.infile[0]:
                files.append(OXOFile(jsFile))

        args.outfile.write(View(args.title, args.description,
                                files, sections).render())
        args.outfile.close()

        # Copy over css and js directories
        outputDirectory = os.path.dirname(args.outfile.name)
        resourceDirectory = os.path.join(os.path.dirname(__file__),
                                         "resources")
        
        cssInputDirectory = os.path.join(resourceDirectory, "css")
        cssOutputDirectory = os.path.join(outputDirectory, "css")
        jsInputDirectory = os.path.join(resourceDirectory, "js")
        jsOutputDirectory = os.path.join(outputDirectory, "js")
        distutils.dir_util.copy_tree(cssInputDirectory, cssOutputDirectory)
        distutils.dir_util.copy_tree(jsInputDirectory, jsOutputDirectory)


class View(pystache.View):
    template_name = "oxo"
    template_path = os.path.join(os.path.dirname(__file__), "resources")
    def __init__(self, title, description, files, sections):
        pystache.View.__init__(self)
        self.pageTitle = title
        self.pageDescription = description
        self.files = files
        self.sections = sections

    def file(self):
        fileList = []
        for jsFile in self.files:
            fileList.append(self.fileDict(jsFile))
        return fileList

    def section(self):
        sectionList = []
        for section in self.sections:
            sectionDict = {}
            sectionList.append(sectionDict)
            sectionDict["title"] = section.title
            fileList = []
            sectionDict["file"] = fileList
            for jsFile in section.files:
                fileList.append(self.fileDict(jsFile))
        return sectionList


    def title(self):
        return self.pageTitle

    def description(self):
        return markdown2.markdown(self.pageDescription)


    def fileDict(self, jsFile):
        fileDict = {}

        fileDict["name"] = jsFile.name
        fileDict["fileName"] = jsFile.fileName

        fileDict["content"] = []
        for section in jsFile.content:
            sectionDict = {}
            fileDict["content"].append(sectionDict)

            sectionDict["code"] = section["code"].formatted()

            commentDict = {}
            sectionDict["comment"] = commentDict

            comment = section["comment"]
            commentDict["body"] = comment.formatted()
            commentDict["tag"] = []

            for tag in comment.tags:
                tagDict = {}
                commentDict["tag"].append(tagDict)
                tagDict["body"] = tag.tag
        return fileDict
                    
class Section:
    def __init__(self, title, files):
        self.title = title
        self.files = []
        for jsFile in files:
            self.files.append(OXOFile(jsFile))
        
class OXOFile:
    def __init__(self, jsFile):
        self.fileName = jsFile.name 
        self.name = os.path.basename(self.fileName)
        self.name = os.path.splitext(self.name)[0]

        text = jsFile.read()
        self.content = []

        self.parse(text)

    def parse(self, text):
        section = {"code": None, "comment": None}
        while 1:
            code, sep, after = text.partition("/*")

            if code.strip():
                section["code"] = Code(code)

            if (section["comment"] or section["code"]):
                self.content.append(section)
                section = {"code": "", "comment": ""}

            if sep is "" and after is "":
                return

            comment, sep, text = after.partition("*/")

            if comment[0] != "!":
                section["comment"] = Comment(comment)

class Code:
    def __init__(self, codeString):
        self.code = ""
        self.parse(codeString)

    def parse(self, code):
        # Not much to do here
        self.code = code.strip()

    def formatted(self):
        return highlight(self.code, JavascriptLexer(), HtmlFormatter())

class Comment:
    def __init__(self, commentString):
        self.body = ""
        self.tags = []
        self.parse(commentString)

    def parse(self, comment):
        # Remove asterisks from the start of lines
        comment = re.sub("^ *\* ?", "", comment, 0, re.MULTILINE)

        # Grab any JSDoc tags
        matches = re.finditer("(^@\w+.*)", comment, re.MULTILINE)

        for match in matches:
            # Remove the tag
            tag = match.groups()[0]
            comment = comment.replace(tag, "", 1)
            self.tags.append(Tag(tag))

        # Remove newlines from the start and end
        comment = comment.strip()

        # Convert single newlines characters into spaces
#        comment = re.sub("(?<!\n)\n(?!\n)", " ", comment, 0, re.MULTILINE)
        self.body = comment

    def formatted(self):
        return markdown2.markdown(self.body)

class Tag:
    def __init__(self, tagString):
        self.tag = ""

        self.parse(tagString)

    def parse(self, tagString):
        parts = tagString.split()
        # Strong the tag name
        parts[0] = "<strong>" + parts[0][1:] + "</strong>"

        # Emphasise and object names
        if len(parts) > 1 and parts[1][0] == "{":
            parts[1] = "<em>" + parts[1][1:-1] + "</em>"

        self.tag = " ".join(parts)

if __name__ == "__main__":
    OXO()
