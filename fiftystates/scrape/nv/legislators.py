import re
import urlparse
import datetime

from fiftystates.scrape import NoDataForYear
from fiftystates.scrape.legislators import LegislatorScraper, Legislator
from fiftystates.scrape.nv.utils import clean_committee_name

import lxml.etree
import urllib

class NVLegislatorScraper(LegislatorScraper):
    state = 'nv'

    def scrape(self, chamber, year):
        self.save_errors=False
        if year < 2001:
            raise NoDataForYear(year)

        time = datetime.datetime.now()
        curyear = time.year
        if ((int(year) - curyear) % 2) == 1:
            session = ((int(year) -  curyear) / 2) + 76
        elif( ((int(year) - curyear) % 2) == 0) and year >= 2010:
            session = ((int(year) - curyear) / 2) + 26
        else:
            raise NoDataForYear(year)

        if chamber == 'upper':
            self.scrape_legislators(chamber, session, year)
        elif chamber == 'lower':
            self.scrape_legislators(chamber, session, year)


    def scrape_legislators(self, chamber, session, year):
       
        sessionsuffix = 'th'
        if str(session)[-1] == '1':
            sessionsuffix = 'st'
        elif str(session)[-1] == '2':
            sessionsuffix = 'nd'
        elif str(session)[-1] == '3':
            sessionsuffix = 'rd'

        insert = str(session) + sessionsuffix + str(year)
        if session == 26:
            insert = str(session) + sessionsuffix + str(year) + "Special"

        if chamber == 'upper':        
            leg_url = 'http://www.leg.state.nv.us/Session/' + insert  + '/legislators/Senators/slist.cfm'
            n = 22
        elif chamber == 'lower':
            leg_url = 'http://www.leg.state.nv.us/Session/' + insert  + '/legislators/Assembly/alist.cfm'
            n = 43

        with self.urlopen(leg_url) as page:
            root = lxml.etree.fromstring(page, lxml.etree.HTMLParser())        

            #Going through the districts
            for numdistricts in range(1, n):
                namepath = 'string(/html/body/table[%s]/tr/td/table[1]/tr/td[2]/font/a)' % (numdistricts + 2)
                last_name = root.xpath(namepath).split()[0]
                last_name = last_name[0 : len(last_name) - 1]
                middle_name = ''

                if len(root.xpath(namepath).split()) == 2:
                    first_name = root.xpath(namepath).split()[1]
                elif len(root.xpath(namepath).split()) == 3:
                    first_name = root.xpath(namepath).split()[1]
                    middle_name = root.xpath(namepath).split()[2]
                elif len(root.xpath(namepath).split()) == 4:
                    first_name = root.xpath(namepath).split()[2]
                    middle_name = root.xpath(namepath).split()[3]
                    last_name = last_name + " " + root.xpath(namepath).split()[1]
                    last_name = last_name[0: len(last_name) - 1]

                if len(middle_name) > 0:
                    full_name = first_name + " " + middle_name + " " + last_name
                else:
                    full_name = first_name + " " + last_name
                 
                partypath = 'string(/html/body/table[%s]/tr/td/table[1]/tr/td[3]/font)' % (numdistricts + 2)
                party = root.xpath(partypath).split()[-1]

                districtpath = 'string(/html/body/table[%s]/tr/td/table[1]/tr/td[4]/font)' % (numdistricts + 2)
                district = root.xpath(districtpath)[11: len(root.xpath(districtpath))]
               
                termpath = 'string(/html/body/table[%s]/tr/td/table[2]/tr/td[5])' % (numdistricts + 2)
                end_date = root.xpath(termpath)[12: 21]
                email = root.xpath(termpath).split()[-1]
                
                addresspath = 'string(/html/body/table[%s]/tr/td/table[2]/tr/td[2])' % (numdistricts + 2)
                address = root.xpath(addresspath)
                address = address
                
                leg = Legislator(session, chamber, district, full_name, first_name, last_name, middle_name, party, end_date = end_date, email = email, address = address)
                leg.add_source(leg_url)
                self.save_legislator(leg)

