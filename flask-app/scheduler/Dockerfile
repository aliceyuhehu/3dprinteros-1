FROM python:3.8

RUN mkdir /srv/scheduler
WORKDIR /srv/scheduler
RUN apt-get update
RUN apt-get install -y supervisor
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
ADD requirements.txt .
RUN pip install -r requirements.txt
ADD . .

#fix openshift permissions
# RUN chgrp -R 0 /src \
#   && chmod -R g+rwX /src

#fix openshift permissions
RUN chgrp -R 0 /srv \
  && chmod -R g+rwX /srv


CMD ["/usr/bin/supervisord"]
