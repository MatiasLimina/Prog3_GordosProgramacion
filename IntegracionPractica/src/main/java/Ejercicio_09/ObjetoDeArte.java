package Ejercicio_09;

import java.util.Objects;

public abstract class ObjetoDeArte {
    private String idIdentificacion;
    private String titulo;
    private String descripcion;
    private Integer anioCreacion; // Integer permite null si no se conoce
    private String paisOrigen;
    private String cultura;
    private String epoca;

    private Artista artista; // Opcional (null si es anónimo)
    private EstadoTenencia estadoTenencia; // Permanente o Prestamo (Composición 1 — 1)

    public ObjetoDeArte(String idIdentificacion, String titulo, String descripcion,
                        Integer anioCreacion, String paisOrigen, String cultura, String epoca,
                        Artista artista, EstadoTenencia estadoTenencia) {
        Objects.requireNonNull(idIdentificacion, "El ID de identificación no puede ser nulo");
        Objects.requireNonNull(titulo, "El título no puede ser nulo");
        Objects.requireNonNull(estadoTenencia, "El estado de tenencia no puede ser nulo");
        this.idIdentificacion = idIdentificacion;
        this.titulo = titulo;
        this.descripcion = descripcion;
        this.anioCreacion = anioCreacion;
        this.paisOrigen = paisOrigen;
        this.cultura = cultura;
        this.epoca = epoca;
        this.artista = artista;
        this.estadoTenencia = estadoTenencia;
    }

    public String getIdIdentificacion() {
        return idIdentificacion;
    }

    public String getTitulo() {
        return titulo;
    }

    public String getDescripcion() {
        return descripcion;
    }

    public Integer getAnioCreacion() {
        return anioCreacion;
    }

    public String getPaisOrigen() {
        return paisOrigen;
    }

    public String getCultura() {
        return cultura;
    }

    public String getEpoca() {
        return epoca;
    }

    public Artista getArtista() {
        return artista;
    }

    public EstadoTenencia getEstadoTenencia() {
        return estadoTenencia;
    }

    public void setEstadoTenencia(EstadoTenencia estadoTenencia) {
        Objects.requireNonNull(estadoTenencia, "El estado de tenencia no puede ser nulo");
        this.estadoTenencia = estadoTenencia;
    }
}
