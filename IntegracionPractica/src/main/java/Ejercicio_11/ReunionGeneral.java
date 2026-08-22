package Ejercicio_11;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Objects;

public class ReunionGeneral {
    private Date fechaUltimaReunion;
    private Date fechaProximaReunion;
    private List<RepresentanteVentas> asistentes; // Asociación N:M con fuerza de ventas

    public ReunionGeneral(Date fechaUltimaReunion, Date fechaProximaReunion) {
        Objects.requireNonNull(fechaUltimaReunion, "La fecha de la última reunión no puede ser nula");
        Objects.requireNonNull(fechaProximaReunion, "La fecha de la próxima reunión no puede ser nula");
        this.fechaUltimaReunion = fechaUltimaReunion;
        this.fechaProximaReunion = fechaProximaReunion;
        this.asistentes = new ArrayList<>();
    }

    public void registrarAsistente(RepresentanteVentas representante) {
        Objects.requireNonNull(representante, "El representante no puede ser nulo");
        if (!asistentes.contains(representante)) {
            asistentes.add(representante);
        }
    }

    public Date getFechaUltimaReunion() {
        return fechaUltimaReunion;
    }

    public void setFechaUltimaReunion(Date fechaUltimaReunion) {
        Objects.requireNonNull(fechaUltimaReunion, "La fecha no puede ser nula");
        this.fechaUltimaReunion = fechaUltimaReunion;
    }

    public Date getFechaProximaReunion() {
        return fechaProximaReunion;
    }

    public void setFechaProximaReunion(Date fechaProximaReunion) {
        Objects.requireNonNull(fechaProximaReunion, "La fecha no puede ser nula");
        this.fechaProximaReunion = fechaProximaReunion;
    }

    public List<RepresentanteVentas> getAsistentes() {
        return Collections.unmodifiableList(asistentes);
    }
}
